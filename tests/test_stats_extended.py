"""
Extended tests for pyshort.stats module covering edge cases and advanced scenarios.
"""
import threading
import time
from datetime import date, timedelta
from pyshort.stats import StatisticsTracker


class TestStatisticsTrackerExtended:
    """Extended test cases for StatisticsTracker class covering edge cases."""

    def test_large_increment_value(self):
        """Test incrementing with a very large count."""
        tracker = StatisticsTracker()
        large_count = 10_000_000
        result = tracker.increment_clicks("test1", large_count)
        assert result == large_count
        assert tracker.get_click_stats("test1") == large_count

    def test_many_url_codes(self):
        """Test tracking statistics for many different URL codes."""
        tracker = StatisticsTracker()
        num_urls = 1000
        
        for i in range(num_urls):
            tracker.increment_clicks(f"url{i}", i + 1)
        
        all_stats = tracker.get_all_url_stats()
        assert len(all_stats) == num_urls
        assert tracker.get_total_clicks() == sum(range(1, num_urls + 1))

    def test_top_urls_with_ties(self):
        """Test that top URLs handles ties correctly."""
        tracker = StatisticsTracker()
        
        # Create multiple URLs with the same click count
        for i in range(5):
            tracker.increment_clicks(f"url{i}", 10)
        
        top = tracker.get_top_urls(limit=3)
        assert len(top) == 3
        # All should have count 10
        for count, _ in top:
            assert count == 10

    def test_top_urls_all_same_count(self):
        """Test top URLs when all URLs have the same count."""
        tracker = StatisticsTracker()
        
        for i in range(10):
            tracker.increment_clicks(f"url{i}", 5)
        
        top = tracker.get_top_urls()
        assert len(top) == 10
        # All should have count 5
        for count, _ in top:
            assert count == 5

    def test_increment_updates_position_correctly(self):
        """Test that incrementing updates URL position in top URLs correctly."""
        tracker = StatisticsTracker()
        
        # Create URLs with different counts
        tracker.increment_clicks("url1", 10)
        tracker.increment_clicks("url2", 20)
        tracker.increment_clicks("url3", 15)
        
        # Verify initial order
        top = tracker.get_top_urls()
        assert top[0][1] == "url2"
        assert top[1][1] == "url3"
        assert top[2][1] == "url1"
        
        # Increment url1 to surpass others
        tracker.increment_clicks("url1", 15)
        
        # Verify new order
        top = tracker.get_top_urls()
        assert top[0][1] == "url1"  # Now 25
        assert top[1][1] == "url2"  # Still 20
        assert top[2][1] == "url3"  # Still 15

    def test_daily_stats_across_multiple_days(self):
        """Test daily statistics across multiple consecutive days."""
        tracker = StatisticsTracker()
        
        # Simulate activity across 7 days
        for day_offset in range(7):
            day = date.today() - timedelta(days=6 - day_offset)
            tracker._daily_clicks[day] = day_offset * 10
        
        # Check each day
        for day_offset in range(7):
            day = date.today() - timedelta(days=6 - day_offset)
            assert tracker.get_daily_stats(day) == day_offset * 10

    def test_stats_summary_multiple_days(self):
        """Test stats summary with multiple days of data."""
        tracker = StatisticsTracker()
        
        # Add data for multiple days
        for i in range(5):
            day = date.today() - timedelta(days=i)
            tracker._daily_clicks[day] = (i + 1) * 10
        
        tracker.increment_clicks("url1", 50)
        tracker.increment_clicks("url2", 30)
        tracker.increment_clicks("url3", 20)
        
        summary = tracker.get_stats_summary()
        assert summary["total_clicks"] == 100
        assert summary["total_urls"] == 3
        assert summary["total_days"] == 6  # 5 historical + today
        assert len(summary["top_urls"]) <= 5

    def test_concurrent_resets(self):
        """Test thread safety of concurrent reset operations."""
        tracker = StatisticsTracker()
        
        # Set up initial data
        for i in range(100):
            tracker.increment_clicks(f"url{i}", i + 1)
        
        # Create threads that reset URLs
        def reset_worker(url_prefix):
            for i in range(10):
                tracker.reset_url_stats(f"{url_prefix}{i}")
        
        threads = []
        for prefix in ["url", "url1", "url2"]:
            t = threading.Thread(target=reset_worker, args=(prefix,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Some URLs should be reset
        all_stats = tracker.get_all_url_stats()
        assert len(all_stats) <= 100

    def test_increment_after_reset(self):
        """Test that incrementing works correctly after resetting a URL."""
        tracker = StatisticsTracker()
        
        tracker.increment_clicks("test1", 10)
        assert tracker.get_click_stats("test1") == 10
        
        tracker.reset_url_stats("test1")
        assert tracker.get_click_stats("test1") == 0
        
        tracker.increment_clicks("test1", 5)
        assert tracker.get_click_stats("test1") == 5

    def test_url_code_with_special_characters(self):
        """Test handling of URL codes with various characters."""
        tracker = StatisticsTracker()
        
        # Test various character combinations
        test_codes = [
            "abc-123",
            "test_123",
            "UPPERCASE",
            "lowercase",
            "MixedCase123",
            "with-dash",
            "with_underscore",
        ]
        
        for code in test_codes:
            tracker.increment_clicks(code, 5)
        
        all_stats = tracker.get_all_url_stats()
        assert len(all_stats) == len(test_codes)
        
        for code in test_codes:
            assert tracker.get_click_stats(code) == 5

    def test_empty_tracker_behavior(self):
        """Test behavior of an empty tracker with all methods."""
        tracker = StatisticsTracker()
        
        assert tracker.get_total_clicks() == 0
        assert tracker.get_daily_stats() == 0
        assert tracker.get_all_url_stats() == {}
        assert tracker.get_all_daily_stats() == {}
        assert tracker.get_top_urls() == []
        
        summary = tracker.get_stats_summary()
        assert summary["total_clicks"] == 0
        assert summary["total_urls"] == 0
        assert summary["total_days"] == 0
        assert summary["top_urls"] == []
        assert summary["today_clicks"] == 0

    def test_top_urls_with_more_urls_than_limit(self):
        """Test top URLs with many more URLs than the limit."""
        tracker = StatisticsTracker()
        
        # Create 50 URLs
        for i in range(50):
            tracker.increment_clicks(f"url{i}", i + 1)
        
        # Get top 10
        top = tracker.get_top_urls(limit=10)
        assert len(top) == 10
        
        # Verify they're the top 10 (url40 to url49 reversed)
        expected_urls = [f"url{i}" for i in range(49, 39, -1)]
        actual_urls = [url for _, url in top]
        assert actual_urls == expected_urls

    def test_get_stats_summary_includes_today(self):
        """Test that stats summary correctly includes today's clicks."""
        tracker = StatisticsTracker()
        
        # Add historical data
        yesterday = date.today() - timedelta(days=1)
        tracker._daily_clicks[yesterday] = 100
        
        # Add today's data
        tracker.increment_clicks("test1", 50)
        
        summary = tracker.get_stats_summary()
        assert summary["today_clicks"] == 50
        assert summary["total_clicks"] == 50  # Only URL clicks, not daily total

    def test_thread_safety_daily_stats(self):
        """Test thread safety of daily statistics updates."""
        tracker = StatisticsTracker()
        num_threads = 10
        increments_per_thread = 100
        
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
        
        # Verify daily stats match total
        daily = tracker.get_daily_stats()
        total = tracker.get_click_stats("test1")
        assert daily == total
        assert daily == num_threads * increments_per_thread

    def test_reset_clears_from_all_methods(self):
        """Test that resetting clears URL from all internal data structures."""
        tracker = StatisticsTracker()
        
        tracker.increment_clicks("test1", 100)
        tracker.increment_clicks("test2", 50)
        
        # Verify it's in all data structures
        assert "test1" in tracker.get_all_url_stats()
        top_urls = [url for _, url in tracker.get_top_urls()]
        assert "test1" in top_urls
        
        # Reset
        tracker.reset_url_stats("test1")
        
        # Verify it's gone from all data structures
        assert "test1" not in tracker.get_all_url_stats()
        top_urls = [url for _, url in tracker.get_top_urls()]
        assert "test1" not in top_urls

    def test_increment_order_preserves_sorting(self):
        """Test that the order of increments doesn't affect final sorting."""
        tracker = StatisticsTracker()
        
        # Increment in different order
        tracker.increment_clicks("url5", 5)
        tracker.increment_clicks("url1", 1)
        tracker.increment_clicks("url3", 3)
        tracker.increment_clicks("url2", 2)
        tracker.increment_clicks("url4", 4)
        
        top = tracker.get_top_urls()
        assert len(top) == 5
        assert [url for _, url in top] == ["url5", "url4", "url3", "url2", "url1"]

    def test_multiple_increments_same_url_different_threads(self):
        """Test multiple threads incrementing the same URL multiple times."""
        tracker = StatisticsTracker()
        num_threads = 5
        increments_per_thread = 20
        
        def increment_worker(thread_id):
            for i in range(increments_per_thread):
                tracker.increment_clicks("test1", 1)
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=increment_worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        expected = num_threads * increments_per_thread
        assert tracker.get_click_stats("test1") == expected
        assert tracker.get_total_clicks() == expected

    def test_get_all_daily_stats_returns_copy(self):
        """Test that get_all_daily_stats returns a copy, not internal data."""
        tracker = StatisticsTracker()
        
        tracker.increment_clicks("test1", 10)
        
        stats1 = tracker.get_all_daily_stats()
        stats2 = tracker.get_all_daily_stats()
        
        # Modify the returned dict
        stats1[date.today()] = 999
        
        # The second dict should not be affected
        assert stats2[date.today()] == 10

    def test_get_all_url_stats_returns_copy(self):
        """Test that get_all_url_stats returns a copy, not internal data."""
        tracker = StatisticsTracker()
        
        tracker.increment_clicks("test1", 10)
        
        stats1 = tracker.get_all_url_stats()
        stats2 = tracker.get_all_url_stats()
        
        # Modify the returned dict
        stats1["test1"] = 999
        
        # The second dict should not be affected
        assert stats2["test1"] == 10

    def test_week_activity_pattern(self):
        """Test tracking activity over a week period."""
        tracker = StatisticsTracker()
        
        # Simulate a week of activity
        for day_offset in range(7):
            day = date.today() - timedelta(days=6 - day_offset)
            
            # Simulate different activity levels per day
            clicks = (day_offset + 1) * 5
            tracker._daily_clicks[day] = clicks
            
            # Also add some URL-specific data
            tracker.increment_clicks(f"url{day_offset}", clicks)
        
        all_daily = tracker.get_all_daily_stats()
        assert len(all_daily) == 7
        
        # Total should match sum of all days
        expected_total = sum((i + 1) * 5 for i in range(7))
        assert tracker.get_daily_stats() >= expected_total

    def test_zero_then_nonzero_increment(self):
        """Test increment behavior going from zero to non-zero."""
        tracker = StatisticsTracker()
        
        # Start with zero count (implicit)
        assert tracker.get_click_stats("test1") == 0
        
        # Add a non-zero increment
        result = tracker.increment_clicks("test1", 5)
        assert result == 5
        assert tracker.get_click_stats("test1") == 5
        
        # Add more
        result = tracker.increment_clicks("test1", 3)
        assert result == 8
        assert tracker.get_click_stats("test1") == 8

    def test_performance_with_many_urls(self):
        """Test that operations remain efficient with many URLs."""
        tracker = StatisticsTracker()
        num_urls = 1000
        
        # Time the increment operations
        start_time = time.time()
        for i in range(num_urls):
            tracker.increment_clicks(f"url{i}", 1)
        increment_time = time.time() - start_time
        
        # Time the get_top_urls operation
        start_time = time.time()
        top = tracker.get_top_urls(limit=10)
        top_time = time.time() - start_time
        
        # Assertions about performance
        assert len(top) == 10
        assert increment_time < 1.0  # Should complete quickly
        assert top_time < 0.1  # Should be very fast

    def test_top_urls_stability(self):
        """Test that top URLs remain stable after equal increments."""
        tracker = StatisticsTracker()
        
        # Create URLs with different counts
        for i in range(5):
            tracker.increment_clicks(f"url{i}", i * 10)
        
        # Get initial top URLs
        top1 = tracker.get_top_urls()
        
        # Increment all by the same amount
        for i in range(5):
            tracker.increment_clicks(f"url{i}", 5)
        
        # Get new top URLs
        top2 = tracker.get_top_urls()
        
        # Order should remain the same
        assert [url for _, url in top1] == [url for _, url in top2]