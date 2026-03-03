"""
Tests for pyshort.stats module.
"""
import threading
import time
from datetime import date, timedelta
from pyshort.stats import StatisticsTracker


class TestStatisticsTracker:
    """Test cases for StatisticsTracker class."""

    def test_initialization(self):
        """Test that StatisticsTracker initializes correctly."""
        tracker = StatisticsTracker()
        assert tracker.get_click_stats("test1") == 0
        assert tracker.get_daily_stats() == 0
        assert tracker.get_top_urls() == []

    def test_increment_clicks_single(self):
        """Test incrementing clicks for a URL once."""
        tracker = StatisticsTracker()
        result = tracker.increment_clicks("test1", 1)
        assert result == 1
        assert tracker.get_click_stats("test1") == 1

    def test_increment_clicks_multiple(self):
        """Test incrementing clicks multiple times."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 5)
        tracker.increment_clicks("test1", 3)
        assert tracker.get_click_stats("test1") == 8

    def test_increment_clicks_zero(self):
        """Test incrementing with zero count."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 5)
        result = tracker.increment_clicks("test1", 0)
        assert result == 5
        assert tracker.get_click_stats("test1") == 5

    def test_increment_clicks_negative_error(self):
        """Test that negative count raises ValueError."""
        tracker = StatisticsTracker()
        try:
            tracker.increment_clicks("test1", -1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "non-negative" in str(e)

    def test_click_stats_for_nonexistent_url(self):
        """Test getting stats for a URL that doesn't exist."""
        tracker = StatisticsTracker()
        assert tracker.get_click_stats("nonexistent") == 0

    def test_daily_stats_today(self):
        """Test getting daily statistics for today."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 5)
        tracker.increment_clicks("test2", 3)
        assert tracker.get_daily_stats() == 8

    def test_daily_stats_specific_day(self):
        """Test getting daily statistics for a specific day."""
        tracker = StatisticsTracker()
        yesterday = date.today() - timedelta(days=1)

        # Manually set yesterday's stats
        tracker._daily_clicks[yesterday] = 10
        assert tracker.get_daily_stats(yesterday) == 10

    def test_all_daily_stats(self):
        """Test getting all daily statistics."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 3)
        
        yesterday = date.today() - timedelta(days=1)
        tracker._daily_clicks[yesterday] = 5

        all_stats = tracker.get_all_daily_stats()
        assert len(all_stats) == 2
        assert all_stats[date.today()] == 3
        assert all_stats[yesterday] == 5

    def test_top_urls_single(self):
        """Test getting top URLs with single URL."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        top = tracker.get_top_urls()
        assert len(top) == 1
        assert top[0] == (10, "test1")

    def test_top_urls_multiple_sorted(self):
        """Test that top URLs are sorted correctly by click count."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)
        tracker.increment_clicks("test3", 5)

        top = tracker.get_top_urls()
        assert len(top) == 3
        assert top[0] == (20, "test2")
        assert top[1] == (10, "test1")
        assert top[2] == (5, "test3")

    def test_top_urls_with_limit(self):
        """Test getting top URLs with a limit."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)
        tracker.increment_clicks("test3", 15)
        tracker.increment_clicks("test4", 5)

        top = tracker.get_top_urls(limit=2)
        assert len(top) == 2
        assert top[0] == (20, "test2")
        assert top[1] == (15, "test3")

    def test_top_urls_zero_limit(self):
        """Test getting top URLs with zero limit."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)

        top = tracker.get_top_urls(limit=0)
        assert top == []

    def test_top_urls_negative_limit(self):
        """Test getting top URLs with negative limit."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)

        top = tracker.get_top_urls(limit=-1)
        assert top == []

    def test_all_url_stats(self):
        """Test getting statistics for all URLs."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)
        tracker.increment_clicks("test3", 5)

        all_stats = tracker.get_all_url_stats()
        assert len(all_stats) == 3
        assert all_stats["test1"] == 10
        assert all_stats["test2"] == 20
        assert all_stats["test3"] == 5

    def test_reset_url_stats(self):
        """Test resetting statistics for a specific URL."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)

        old_count = tracker.reset_url_stats("test1")
        assert old_count == 10
        assert tracker.get_click_stats("test1") == 0
        assert tracker.get_click_stats("test2") == 20

    def test_reset_nonexistent_url(self):
        """Test resetting stats for a non-existent URL."""
        tracker = StatisticsTracker()
        old_count = tracker.reset_url_stats("nonexistent")
        assert old_count == 0

    def test_reset_url_stats_updates_top_urls(self):
        """Test that resetting URL stats removes it from top URLs."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)
        tracker.increment_clicks("test3", 5)

        assert len(tracker.get_top_urls()) == 3

        tracker.reset_url_stats("test2")

        top = tracker.get_top_urls()
        assert len(top) == 2
        assert top[0] == (10, "test1")
        assert top[1] == (5, "test3")

    def test_get_total_clicks(self):
        """Test getting total clicks across all URLs."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)
        tracker.increment_clicks("test3", 5)

        assert tracker.get_total_clicks() == 35

    def test_get_stats_summary(self):
        """Test getting comprehensive statistics summary."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 20)
        tracker.increment_clicks("test3", 5)

        summary = tracker.get_stats_summary()
        assert summary["total_clicks"] == 35
        assert summary["total_urls"] == 3
        assert summary["total_days"] == 1
        assert len(summary["top_urls"]) <= 5
        assert summary["today_clicks"] == 35

    def test_multiple_increments_same_day(self):
        """Test that multiple increments on same day are aggregated correctly."""
        tracker = StatisticsTracker()
        tracker.increment_clicks("test1", 5)
        tracker.increment_clicks("test1", 3)
        tracker.increment_clicks("test2", 2)

        assert tracker.get_daily_stats() == 10

    def test_top_urls_after_multiple_increments(self):
        """Test that top URLs list is updated correctly after multiple increments."""
        tracker = StatisticsTracker()

        # Initial state
        tracker.increment_clicks("test1", 10)
        tracker.increment_clicks("test2", 5)
        assert tracker.get_top_urls()[0] == (10, "test1")

        # test2 overtakes test1
        tracker.increment_clicks("test2", 10)
        top = tracker.get_top_urls()
        assert top[0] == (15, "test2")
        assert top[1] == (10, "test1")

    def test_thread_safety_single_url(self):
        """Test thread safety with multiple threads incrementing the same URL."""
        tracker = StatisticsTracker()
        num_threads = 10
        increments_per_thread = 1000

        def increment_worker():
            for _ in range(increments_per_thread):
                tracker.increment_clicks("test1", 1)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=increment_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        expected = num_threads * increments_per_thread
        assert tracker.get_click_stats("test1") == expected

    def test_thread_safety_multiple_urls(self):
        """Test thread safety with multiple threads incrementing different URLs."""
        tracker = StatisticsTracker()
        num_threads = 5
        urls = ["test1", "test2", "test3", "test4", "test5"]

        def increment_worker(url_code):
            for _ in range(100):
                tracker.increment_clicks(url_code, 1)

        threads = []
        for i, url_code in enumerate(urls):
            t = threading.Thread(target=increment_worker, args=(url_code,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Each URL should have been incremented by its own thread
        for url_code in urls:
            assert tracker.get_click_stats(url_code) == 100

    def test_thread_safety_concurrent_read_write(self):
        """Test thread safety with concurrent reads and writes."""
        tracker = StatisticsTracker()
        num_writer_threads = 5
        num_reader_threads = 5
        iterations = 100

        def writer_worker():
            for i in range(iterations):
                tracker.increment_clicks("test1", 1)
                tracker.increment_clicks("test2", 1)

        def reader_worker():
            for _ in range(iterations):
                # These reads should not cause race conditions
                stats1 = tracker.get_click_stats("test1")
                stats2 = tracker.get_click_stats("test2")
                top = tracker.get_top_urls()
                total = tracker.get_total_clicks()
                # Just verify we can read without errors
                assert isinstance(stats1, int)
                assert isinstance(stats2, int)
                assert isinstance(top, list)
                assert isinstance(total, int)

        threads = []
        # Start writer threads
        for _ in range(num_writer_threads):
            t = threading.Thread(target=writer_worker)
            threads.append(t)
            t.start()

        # Start reader threads
        for _ in range(num_reader_threads):
            t = threading.Thread(target=reader_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify final state
        expected_each = num_writer_threads * iterations
        assert tracker.get_click_stats("test1") == expected_each
        assert tracker.get_click_stats("test2") == expected_each
        assert tracker.get_total_clicks() == expected_each * 2

    def test_thread_safety_top_urls(self):
        """Test that top URLs sorting remains correct under concurrent access."""
        tracker = StatisticsTracker()
        urls = [f"url{i}" for i in range(10)]

        def increment_worker(start_idx):
            for _ in range(100):
                for i in range(start_idx, start_idx + 5):
                    url_code = urls[i % len(urls)]
                    tracker.increment_clicks(url_code, 1)

        threads = []
        for i in range(5):
            t = threading.Thread(target=increment_worker, args=(i * 2,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify all URLs have counts
        all_stats = tracker.get_all_url_stats()
        assert len(all_stats) == 10

        # Verify top URLs are sorted correctly
        top = tracker.get_top_urls(limit=10)
        for i in range(len(top) - 1):
            assert top[i][0] >= top[i + 1][0], "Top URLs should be sorted descending"