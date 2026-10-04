// Run button instant loading state handler
(function () {
    // 1. Instant click handler on native DOM (capture phase)
    document.addEventListener("click", function (e) {
        const btn = e.target.closest("#run-button");
        if (btn && !btn.classList.contains("is-running")) {
            // Instantly transition visual state to Running with animated circle
            btn.classList.add("is-running");
            btn.setAttribute("data-running", "true");

            // Prevent double-clicking after the current click event dispatches
            setTimeout(function () {
                if (btn && btn.classList.contains("is-running")) {
                    btn.style.pointerEvents = "none";
                }
            }, 60);
        }
    }, true);

    function resetButton() {
        const btn = document.getElementById("run-button");
        if (btn) {
            btn.classList.remove("is-running");
            btn.removeAttribute("data-running");
            btn.style.pointerEvents = "auto";
        }
    }

    // 2. Observer to detect when decisions panel finishes rendering
    let currentObserved = null;
    function checkAndObserve() {
        const panel = document.getElementById("decisions-panel-content");
        if (panel && panel !== currentObserved) {
            currentObserved = panel;
            const observer = new MutationObserver(function () {
                resetButton();
            });
            observer.observe(panel, { childList: true, subtree: false });
        }
    }

    // Initialize observer
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            checkAndObserve();
            setInterval(checkAndObserve, 400);
        });
    } else {
        checkAndObserve();
        setInterval(checkAndObserve, 400);
    }
})();
