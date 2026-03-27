/**
 * notif-live.js — Live notification badge updater
 * Polls /api/notification-count/ every 30s and updates all .notif-badge elements.
 * Also fires immediately on page focus (returning from notifications page).
 */
(function () {
    'use strict';

    function updateBadges(count) {
        var badges = document.querySelectorAll('.notif-badge');
        badges.forEach(function (b) {
            if (count > 0) {
                b.textContent = count > 99 ? '99+' : count;
                b.style.display = 'flex';
            } else {
                b.style.display = 'none';
            }
        });
        // Also update sidebar nav badge spans with class notif-nav-count
        document.querySelectorAll('.notif-nav-count').forEach(function (b) {
            if (count > 0) {
                b.textContent = count;
                b.style.display = 'inline';
            } else {
                b.style.display = 'none';
            }
        });
    }

    function fetchCount() {
        fetch('/api/notification-count/', { credentials: 'same-origin' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) { if (d !== null) updateBadges(d.count); })
            .catch(function () { /* silent fail */ });
    }

    // Run on load
    fetchCount();

    // Run every 30 seconds
    setInterval(fetchCount, 30000);

    // Run immediately when user returns to this tab (e.g. came back from notifications page)
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') fetchCount();
    });

    // Run on window focus
    window.addEventListener('focus', fetchCount);
}());
