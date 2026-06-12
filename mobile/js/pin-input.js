/**
 * TurboShare — 6-digit PIN input component.
 *
 * Creates 6 individual input boxes with auto-advance, backspace
 * navigation, and paste support. Uses inputmode="numeric" for
 * mobile number keyboards.
 */

(function () {
    'use strict';

    const container = document.getElementById('pin-container');
    if (!container) return;

    const PIN_LENGTH = 6;
    const boxes = [];

    // Create 6 input boxes
    for (let i = 0; i < PIN_LENGTH; i++) {
        const input = document.createElement('input');
        input.type = 'text';
        input.inputMode = 'numeric';
        input.pattern = '[0-9]';
        input.maxLength = 1;
        input.className = 'pin-box';
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('data-index', i.toString());

        input.addEventListener('input', onInput);
        input.addEventListener('keydown', onKeyDown);
        input.addEventListener('paste', onPaste);
        input.addEventListener('focus', onFocus);

        container.appendChild(input);
        boxes.push(input);
    }

    function onInput(e) {
        const idx = parseInt(this.dataset.index);
        const val = this.value.replace(/\D/g, '');
        this.value = val.slice(0, 1);

        clearError();

        if (val && idx < PIN_LENGTH - 1) {
            boxes[idx + 1].focus();
        }

        checkComplete();
    }

    function onKeyDown(e) {
        const idx = parseInt(this.dataset.index);

        if (e.key === 'Backspace') {
            if (!this.value && idx > 0) {
                boxes[idx - 1].focus();
                boxes[idx - 1].value = '';
            }
        } else if (e.key === 'ArrowLeft' && idx > 0) {
            boxes[idx - 1].focus();
        } else if (e.key === 'ArrowRight' && idx < PIN_LENGTH - 1) {
            boxes[idx + 1].focus();
        }
    }

    function onPaste(e) {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData)
            .getData('text')
            .replace(/\D/g, '')
            .slice(0, PIN_LENGTH);

        for (let i = 0; i < text.length; i++) {
            boxes[i].value = text[i];
        }

        const nextIdx = Math.min(text.length, PIN_LENGTH - 1);
        boxes[nextIdx].focus();
        checkComplete();
    }

    function onFocus() {
        this.select();
    }

    function checkComplete() {
        const pin = getPin();
        const confirmBtn = document.getElementById('btn-confirm');
        if (confirmBtn) {
            confirmBtn.disabled = pin.length < PIN_LENGTH;
        }
    }

    // ── Public API ──────────────────────────────────────────────

    window.PinInput = {
        getPin: getPin,
        clear: clear,
        showError: showError,
        clearError: clearError,
    };

    function getPin() {
        return boxes.map(b => b.value).join('');
    }

    function clear() {
        boxes.forEach(b => { b.value = ''; });
        boxes[0].focus();
        checkComplete();
    }

    function showError(msg) {
        boxes.forEach(b => b.classList.add('error'));
        const errEl = document.getElementById('pin-error');
        if (errEl) {
            errEl.textContent = msg;
            errEl.style.display = 'block';
        }
        setTimeout(() => {
            boxes.forEach(b => b.classList.remove('error'));
        }, 500);
    }

    function clearError() {
        boxes.forEach(b => b.classList.remove('error'));
        const errEl = document.getElementById('pin-error');
        if (errEl) errEl.style.display = 'none';
    }
})();
