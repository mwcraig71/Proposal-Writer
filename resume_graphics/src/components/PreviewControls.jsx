import React from 'react';
import { SIZE_PRESETS } from '../lib/constants';

export default function PreviewControls({ sizePreset, setSizePreset, widthOverride, setWidthOverride, fontScale, setFontScale }) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm">
      <div className="flex items-center gap-2">
        <span className="text-slate-500 font-medium">Spacing:</span>
        <div className="flex rounded-md overflow-hidden border border-slate-300">
          {Object.keys(SIZE_PRESETS).map((key) => (
            <button
              key={key}
              onClick={() => {
                setSizePreset(key);
                setWidthOverride(SIZE_PRESETS[key].baseWidth);
              }}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                sizePreset === key
                  ? 'bg-[#cf3910] text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100'
              }`}
            >
              {SIZE_PRESETS[key].label}
            </button>
          ))}
        </div>
      </div>

      <span className="text-xs font-semibold text-slate-400 bg-slate-200 px-2 py-1 rounded">300 DPI</span>

      <div className="flex items-center gap-2">
        <label className="text-slate-500 font-medium">Width:</label>
        <input
          type="number"
          value={widthOverride}
          onChange={(e) => setWidthOverride(Number(e.target.value))}
          className="w-20 px-2 py-1.5 border border-slate-300 rounded text-center text-sm"
          min={200}
          max={1200}
        />
        <span className="text-slate-400 text-xs">px</span>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-slate-500 font-medium">Font Size:</label>
        <input
          type="range"
          min={50}
          max={200}
          value={fontScale}
          onChange={(e) => setFontScale(Number(e.target.value))}
          className="w-24 accent-[#cf3910]"
        />
        <span className="text-slate-600 font-medium w-10 text-center">{fontScale}%</span>
      </div>
    </div>
  );
}
