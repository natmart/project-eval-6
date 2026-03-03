"""
Statistics tracking for pyshort URL shortener.

This module provides thread-safe statistics tracking for URL clicks,
including daily statistics and top URLs by click count.
"""
import threading
from collections import defaultdict
from datetime import datetime, date
from typing import Dict, List, Any


class StatisticsTracker:
    """
    Thread-safe tracker for URL statistics.

    Tracks clicks per URL, daily statistics (date -> count),
    and maintains a list of top URLs by click count.

    Attributes:
        url_clicks: Dictionary mapping URL codes to click counts
        daily_clicks: Dictionary mapping dates to total click counts
        top_urls: List of (count, url_code) tuples sorted by count (descending)
        lock: Threading lock for thread-safe operations
    """

    def __init__(self) -> None:
        """
        Initialize a new StatisticsTracker.
        """
        self._url_clicks: Dict[str, int] = defaultdict(int)
        self._daily_clicks: Dict[date, int] = defaultdict(int)
        self._top_urls: List[tuple] = []
        self._lock = threading.Lock()
        self._url_to_index: Dict[str, int] = {}

    def increment_clicks(self, url_code: str, count: int = 1) -> int:
        """
        Increment the click count for a URL in a thread-safe manner.

        Args:
            url_code: The short code of the URL
            count: Number of clicks to increment by (defaults to 1)

        Returns:
            The new click count for this URL

        Raises:
            ValueError: If count is negative
        """
        if count < 0:
            raise ValueError("count must be non-negative")

        if count == 0:
            return self.get_click_stats(url_code)

        today = date.today()

        with self._lock:
            # Update URL click count
            old_count = self._url_clicks[url_code]
            new_count = old_count + count
            self._url_clicks[url_code] = new_count

            # Update daily click count
            self._daily_clicks[today] += count

            # Update top URLs list
            # If URL already exists, remove it first
            if url_code in self._url_to_index:
                idx = self._url_to_index[url_code]
                if idx < len(self._top_urls):
                    # Remove the old entry
                    del self._top_urls[idx]
                    # Update indices for entries that shifted
                    for i in range(idx, len(self._top_urls)):
                        _, other_url = self._top_urls[i]
                        self._url_to_index[other_url] = i

            # Find correct position in descending order using binary search
            left, right = 0, len(self._top_urls)
            while left < right:
                mid = (left + right) // 2
                if new_count > self._top_urls[mid][0]:
                    right = mid
                else:
                    left = mid + 1

            # Insert at the correct position
            self._top_urls.insert(left, (new_count, url_code))

            # Update index mapping
            for i in range(left, len(self._top_urls)):
                _, url = self._top_urls[i]
                self._url_to_index[url] = i

            return new_count

    def get_click_stats(self, url_code: str) -> int:
        """
        Get the click count for a specific URL.

        Args:
            url_code: The short code of the URL

        Returns:
            The click count for this URL (0 if URL not tracked)
        """
        with self._lock:
            return self._url_clicks.get(url_code, 0)

    def get_daily_stats(self, day: date = None) -> int:
        """
        Get the click count for a specific day.

        Args:
            day: The date to get statistics for (defaults to today)

        Returns:
            The click count for the specified day (0 if day not tracked)
        """
        if day is None:
            day = date.today()

        with self._lock:
            return self._daily_clicks.get(day, 0)

    def get_all_daily_stats(self) -> Dict[date, int]:
        """
        Get all daily statistics.

        Returns:
            Dictionary mapping dates to click counts
        """
        with self._lock:
            return dict(self._daily_clicks)

    def get_top_urls(self, limit: int = 10) -> List[tuple]:
        """
        Get the top URLs by click count.

        Args:
            limit: Maximum number of URLs to return (defaults to 10)

        Returns:
            List of (count, url_code) tuples sorted by count descending
        """
        if limit <= 0:
            return []

        with self._lock:
            return self._top_urls[:limit]

    def get_all_url_stats(self) -> Dict[str, int]:
        """
        Get click statistics for all tracked URLs.

        Returns:
            Dictionary mapping URL codes to click counts
        """
        with self._lock:
            return dict(self._url_clicks)

    def reset_url_stats(self, url_code: str) -> int:
        """
        Reset the click count for a specific URL to 0.

        Args:
            url_code: The short code of the URL

        Returns:
            The previous click count (0 if URL was not tracked)
        """
        with self._lock:
            old_count = self._url_clicks.pop(url_code, 0)

            # Remove from top URLs list
            if url_code in self._url_to_index:
                idx = self._url_to_index[url_code]
                if idx < len(self._top_urls):
                    del self._top_urls[idx]
                    del self._url_to_index[url_code]
                    # Update indices for entries that shifted
                    for i in range(idx, len(self._top_urls)):
                        _, other_url = self._top_urls[i]
                        self._url_to_index[other_url] = i

            return old_count

    def get_total_clicks(self) -> int:
        """
        Get the total clicks across all URLs and all days.

        Returns:
            Total number of clicks tracked
        """
        with self._lock:
            return sum(self._url_clicks.values())

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of statistics.

        Returns:
            Dictionary containing:
            - total_clicks: Total clicks across all URLs
            - total_urls: Number of unique URLs tracked
            - total_days: Number of days with recorded activity
            - top_urls: Top 5 URLs by click count
            - today_clicks: Click count for today
        """
        with self._lock:
            return {
                "total_clicks": sum(self._url_clicks.values()),
                "total_urls": len(self._url_clicks),
                "total_days": len(self._daily_clicks),
                "top_urls": self._top_urls[:5],
                "today_clicks": self._daily_clicks.get(date.today(), 0),
            }


__all__ = ["StatisticsTracker"]