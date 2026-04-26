/**
 * Site-wide font presets. Components use --font-display, --font-body, and
 * --font-mono from global.css; setting documentElement.fontFamily does not
 * override those, so we update the CSS variables instead.
 */

export const FONT_STORAGE_KEY = 'fontFamily';

/** Preset ids stored in localStorage */
export const FONT_PRESETS = {
  NORMAL: 'normal',
  SERIF: 'serif',
  ROUNDED: 'rounded',
};

/** Map legacy keys from older builds */
export function normalizeFontPreset(stored) {
  if (!stored || stored === 'system') return FONT_PRESETS.NORMAL;
  if (stored === FONT_PRESETS.SERIF || stored === FONT_PRESETS.ROUNDED) return stored;
  if (stored === 'mono') return FONT_PRESETS.NORMAL;
  return FONT_PRESETS.NORMAL;
}

const SERIF_DISPLAY =
  '"Playfair Display", Georgia, "Times New Roman", Times, serif';
const SERIF_BODY =
  'Georgia, Cambria, "Palatino Linotype", Palatino, "Book Antiqua", serif';
const SERIF_MONO =
  '"JetBrains Mono", "SF Mono", Consolas, "Courier New", monospace';

const ROUNDED_DISPLAY =
  '"Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
const ROUNDED_BODY =
  '"Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const ROUNDED_MONO =
  '"JetBrains Mono", "SF Mono", "Courier New", monospace';

/**
 * Applies a font preset to :root (CSS variables + clears legacy fontFamily).
 */
export function applyFontFamilyPreset(preset) {
  const root = document.documentElement;
  const key = normalizeFontPreset(preset);

  root.style.removeProperty('font-family');

  if (key === FONT_PRESETS.NORMAL) {
    root.style.removeProperty('--font-display');
    root.style.removeProperty('--font-body');
    root.style.removeProperty('--font-mono');
    return;
  }

  if (key === FONT_PRESETS.SERIF) {
    root.style.setProperty('--font-display', SERIF_DISPLAY);
    root.style.setProperty('--font-body', SERIF_BODY);
    root.style.setProperty('--font-mono', SERIF_MONO);
    return;
  }

  if (key === FONT_PRESETS.ROUNDED) {
    root.style.setProperty('--font-display', ROUNDED_DISPLAY);
    root.style.setProperty('--font-body', ROUNDED_BODY);
    root.style.setProperty('--font-mono', ROUNDED_MONO);
    return;
  }

  root.style.removeProperty('--font-display');
  root.style.removeProperty('--font-body');
  root.style.removeProperty('--font-mono');
}
