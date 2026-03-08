from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, TypeVar

T = TypeVar('T')


@dataclass(slots=True)
class ProgressReporter:
    enabled: bool = True
    total_steps: int | None = None
    current_step: int = 0

    def step(self, message: str) -> None:
        if not self.enabled:
            return
        self.current_step += 1
        if self.total_steps:
            percent = int((self.current_step / self.total_steps) * 100)
            print(f"[obstagoon] [{self.current_step}/{self.total_steps}] {percent:>3}% {message}")
        else:
            print(f"[obstagoon] {message}")

    def info(self, message: str) -> None:
        if self.enabled:
            print(f"[obstagoon] {message}")

    def iter(self, items: Iterable[T], label: str, total: int | None = None, every: int = 25, detail: Callable[[T], str] | None = None, per_item: bool = False) -> Iterator[T]:
        if not self.enabled:
            yield from items
            return
        if total is None:
            try:
                total = len(items)  # type: ignore[arg-type]
            except Exception:
                total = None
        if total and every <= 0:
            every = max(1, total // 100)
        count = 0
        last_percent = -1
        for item in items:
            count += 1
            item_detail = ''
            if detail is not None:
                try:
                    item_detail = str(detail(item)).encode('ascii', errors='replace').decode('ascii')
                except Exception:
                    item_detail = ''
            if total:
                percent = int((count / total) * 100)
                should_print = per_item or count == 1 or count == total or count % every == 0 or percent != last_percent
                if should_print:
                    suffix = f' - {item_detail}' if item_detail else ''
                    print(f"[obstagoon]     {label}: {count}/{total} ({percent}%){suffix}")
                    last_percent = percent
            else:
                if per_item or count == 1 or count % every == 0:
                    suffix = f' - {item_detail}' if item_detail else ''
                    print(f"[obstagoon]     {label}: {count}{suffix}")
            yield item
