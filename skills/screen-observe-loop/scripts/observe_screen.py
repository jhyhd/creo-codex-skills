#!/usr/bin/env python3
"""Bounded Windows screen capture. Standard library only; no UI input actions."""
from __future__ import annotations

import argparse
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import uuid
import zlib


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def png_bytes(width, height, bgra):
    rgb = bytearray(width * height * 3)
    rgb[0::3], rgb[1::3], rgb[2::3] = bgra[2::4], bgra[1::4], bgra[0::4]
    stride = width * 3
    scanlines = b''.join(b'\x00' + rgb[y*stride:(y+1)*stride] for y in range(height))

    def chunk(kind, payload):
        return struct.pack('!I', len(payload)) + kind + payload + struct.pack('!I', zlib.crc32(kind + payload) & 0xffffffff)

    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scanlines, 3)) + chunk(b'IEND', b''))


class Desktop:
    def __init__(self):
        if sys.platform != 'win32':
            raise RuntimeError('Screen capture requires an interactive Windows desktop.')
        self.u = C.WinDLL('user32', use_last_error=True)
        self.g = C.WinDLL('gdi32', use_last_error=True)
        self.u.GetDC.argtypes, self.u.GetDC.restype = [W.HWND], W.HDC
        self.u.ReleaseDC.argtypes = [W.HWND, W.HDC]
        self.u.GetForegroundWindow.restype = W.HWND
        self.u.GetWindowRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
        self.u.GetWindowTextLengthW.argtypes = [W.HWND]
        self.u.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, C.c_int]
        for name in ('IsWindow', 'IsWindowVisible', 'IsIconic'):
            getattr(self.u, name).argtypes = [W.HWND]
        self.g.CreateCompatibleDC.argtypes, self.g.CreateCompatibleDC.restype = [W.HDC], W.HDC
        self.g.SelectObject.argtypes, self.g.SelectObject.restype = [W.HDC, W.HGDIOBJ], W.HGDIOBJ
        self.g.DeleteObject.argtypes = [W.HGDIOBJ]
        self.g.DeleteDC.argtypes = [W.HDC]
        self.g.GdiFlush.argtypes, self.g.GdiFlush.restype = [], W.BOOL
        self.g.BitBlt.argtypes = [W.HDC, C.c_int, C.c_int, C.c_int, C.c_int, W.HDC, C.c_int, C.c_int, W.DWORD]
        self.g.CreateDIBSection.argtypes = [W.HDC, C.c_void_p, W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD]
        self.g.CreateDIBSection.restype = W.HBITMAP
        try:
            self.u.SetProcessDpiAwarenessContext.argtypes = [C.c_void_p]
            self.u.SetProcessDpiAwarenessContext(C.c_void_p(-4))
        except AttributeError:
            self.u.SetProcessDPIAware()

    def title(self, hwnd):
        buf = C.create_unicode_buffer(self.u.GetWindowTextLengthW(hwnd) + 1)
        self.u.GetWindowTextW(hwnd, buf, len(buf))
        return buf.value

    def windows(self):
        result = []
        callback_type = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

        @callback_type
        def visit(hwnd, _):
            if self.u.IsWindowVisible(hwnd):
                title = self.title(hwnd)
                if title:
                    result.append({'hwnd': int(hwnd), 'title': title, 'minimized': bool(self.u.IsIconic(hwnd))})
            return True

        self.u.EnumWindows.argtypes = [callback_type, W.LPARAM]
        if not self.u.EnumWindows(visit, 0):
            raise C.WinError(C.get_last_error())
        return result

    def choose_window(self, title):
        matches = [w for w in self.windows() if title.casefold() in w['title'].casefold()]
        if len(matches) != 1:
            raise RuntimeError(f'Expected one window matching {title!r}; found {len(matches)}. Use --list-windows and a more specific title.')
        return matches[0]['hwnd']

    def bounds(self, args, hwnd):
        sx, sy, sw, sh = (self.u.GetSystemMetrics(i) for i in (76, 77, 78, 79))
        if not sw or not sh:
            raise RuntimeError('No interactive display is available.')
        title = None
        if hwnd:
            if not self.u.IsWindow(hwnd) or not self.u.IsWindowVisible(hwnd) or self.u.IsIconic(hwnd):
                raise RuntimeError('Target window is gone, hidden, or minimized. Capture stopped.')
            title = self.title(hwnd)
            if args.window_title.casefold() not in title.casefold():
                raise RuntimeError('Target window title changed outside the requested scope. Capture stopped.')
            rect = W.RECT()
            if not self.u.GetWindowRect(hwnd, C.byref(rect)):
                raise C.WinError(C.get_last_error())
            original = (rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top)
        else:
            original = tuple(args.region) if args.region else (sx, sy, sw, sh)
        x, y, width, height = original
        left, top = max(x, sx), max(y, sy)
        right, bottom = min(x+width, sx+sw), min(y+height, sy+sh)
        if right <= left or bottom <= top:
            raise RuntimeError('Requested capture area is outside the visible desktop.')
        bounds = (left, top, right-left, bottom-top)
        if bounds[2] * bounds[3] > 40_000_000:
            raise RuntimeError('Capture exceeds 40 million pixels; choose a window or smaller --region.')
        return bounds, {'hwnd': hwnd, 'title': title, 'clipped_to_desktop': bounds != original,
                        'target_is_foreground': bool(hwnd and self.u.GetForegroundWindow() == hwnd)}

    def grab(self, bounds):
        x, y, width, height = bounds
        # BITMAPINFOHEADER with a top-down 32-bit DIB; no third-party encoder.
        info = struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 32, 0, width*height*4, 0, 0, 0, 0)
        info_buffer = C.create_string_buffer(info)
        screen = self.u.GetDC(None)
        memory = self.g.CreateCompatibleDC(screen)
        bitmap = old = None
        try:
            if not screen or not memory:
                raise RuntimeError('Cannot acquire desktop graphics context.')
            bits = C.c_void_p()
            bitmap = self.g.CreateDIBSection(screen, info_buffer, 0, C.byref(bits), None, 0)
            if not bitmap or not bits.value:
                raise RuntimeError('Cannot allocate capture bitmap.')
            old = self.g.SelectObject(memory, bitmap)
            if not self.g.BitBlt(memory, 0, 0, width, height, screen, x, y, 0x40CC0020):
                raise C.WinError(C.get_last_error())
            if not self.g.GdiFlush():
                raise RuntimeError('Desktop graphics capture did not finish successfully.')
            return C.string_at(bits, width*height*4)
        finally:
            if old:
                self.g.SelectObject(memory, old)
            if bitmap:
                self.g.DeleteObject(bitmap)
            if memory:
                self.g.DeleteDC(memory)
            if screen:
                self.u.ReleaseDC(None, screen)


def atomic_write(path, data):
    pending = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    pending.write_bytes(data)
    os.replace(pending, path)


def run(args):
    desktop = Desktop()
    if args.list_windows:
        print(json.dumps({'windows': desktop.windows()}, ensure_ascii=True), flush=True)
        return 0
    hwnd = desktop.choose_window(args.window_title) if args.window_title else None
    run_id = uuid.uuid4().hex[:12]
    output = Path(args.output_dir) if args.output_dir else Path(tempfile.gettempdir()) / 'screen-observe' / run_id
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stop_file = Path(args.stop_file).resolve() if args.stop_file else None
    start = time.monotonic()
    previous = None
    frames = samples = 0

    def emit(event):
        event = {'run_id': run_id, 'at': now(), **event}
        with (output / 'events.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps(event, ensure_ascii=True) + '\n')
        print(json.dumps(event, ensure_ascii=True), flush=True)

    emit({'event': 'started', 'mode': args.mode, 'output_dir': str(output), 'duration': args.duration,
          'interval': args.interval, 'stop_file': str(stop_file) if stop_file else None})
    reason = 'duration'
    try:
        while True:
            if stop_file and stop_file.exists():
                reason = 'stop_file'
                break
            if args.mode == 'watch' and time.monotonic() - start >= args.duration:
                break
            sample_start = time.monotonic()
            bounds, target = desktop.bounds(args, hwnd)
            bgra = desktop.grab(bounds)
            samples += 1
            digest = hashlib.sha256(struct.pack('<4i', *bounds) + bgra).hexdigest()
            if digest != previous:
                frames += 1
                image = png_bytes(bounds[2], bounds[3], bgra)
                frame = output / f'frame_{run_id}_{frames:06d}.png'
                frame.write_bytes(image)
                atomic_write(output / 'latest.png', image)
                metadata = {'event': 'frame', 'run_id': run_id, 'captured_at': now(), 'sequence': frames,
                            'sample': samples, 'sha256': digest, 'width': bounds[2], 'height': bounds[3],
                            'bounds': list(bounds), 'target': target, 'path': str(frame),
                            'latest_image': str(output / 'latest.png')}
                atomic_write(output / 'latest.json', (json.dumps(metadata, ensure_ascii=True, indent=2) + '\n').encode('utf-8'))
                emit(metadata)
                previous = digest
            if args.mode == 'capture':
                reason = 'single_capture'
                break
            if frames >= args.max_frames:
                reason = 'max_frames'
                break
            # Short waits keep --stop-file and Ctrl+C responsive.
            next_sample = sample_start + args.interval
            while time.monotonic() < next_sample and time.monotonic() - start < args.duration:
                if stop_file and stop_file.exists():
                    break
                time.sleep(min(0.1, max(0, next_sample-time.monotonic())))
    except KeyboardInterrupt:
        reason = 'interrupted'
    except Exception as error:
        emit({'event': 'error', 'message': str(error), 'frames': frames, 'samples': samples})
        return 1
    emit({'event': 'stopped', 'reason': reason, 'frames': frames, 'samples': samples,
          'elapsed_seconds': round(time.monotonic()-start, 3)})
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=['capture', 'watch'], default='capture')
    parser.add_argument('--list-windows', action='store_true')
    parser.add_argument('--output-dir', help='Defaults to a unique directory under the system temporary directory.')
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--window-title', help='Case-insensitive substring; exactly one visible window must match.')
    scope.add_argument('--region', type=int, nargs=4, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'))
    parser.add_argument('--interval', type=float, default=2.0, help='Sampling interval in seconds; minimum 0.5.')
    parser.add_argument('--duration', type=float, default=30.0, help='Maximum watch duration in seconds; maximum 300.')
    parser.add_argument('--max-frames', type=int, default=60, help='Maximum saved change frames, from 1 to 600.')
    parser.add_argument('--stop-file', help='Stop promptly when this file exists; not created or deleted by the helper.')
    args = parser.parse_args()
    if not 0.5 <= args.interval <= 300 or not 0 < args.duration <= 300 or not 1 <= args.max_frames <= 600:
        parser.error('Use interval 0.5..300, duration >0..300, and max-frames 1..600.')
    if args.region and (args.region[2] <= 0 or args.region[3] <= 0):
        parser.error('Region width and height must be positive.')
    try:
        return run(args)
    except Exception as error:
        print(json.dumps({'event': 'error', 'message': str(error)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
