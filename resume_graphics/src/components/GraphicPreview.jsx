import React from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { SIZE_PRESETS } from '../lib/constants';

export default function GraphicPreview({ pairs, title, sizePreset, widthOverride, fontScale, previewRef }) {
  const s = SIZE_PRESETS[sizePreset] || SIZE_PRESETS.medium;
  const scale = (fontScale || 100) / 100;
  const width = widthOverride || s.baseWidth;

  return (
    <div
      ref={previewRef}
      style={{
        width: `${width}px`,
        backgroundColor: '#ffffff',
        padding: `${s.containerPadding}px`,
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
      }}
    >
      <div
        style={{
          borderLeft: `${s.titleBorderWidth}px solid #cf3910`,
          paddingLeft: `${8}px`,
          paddingBottom: `${s.titlePaddingBottom}px`,
          marginBottom: `${s.titleMarginBottom}px`,
        }}
      >
        <span
          style={{
            fontSize: `${s.titleFontSize * scale}px`,
            fontWeight: 700,
            letterSpacing: `${s.titleLetterSpacing}px`,
            textTransform: 'uppercase',
            color: '#1e293b',
          }}
        >
          {title || 'CHALLENGE / SOLUTION'}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: `${s.pairGap}px` }}>
        {(pairs || []).filter(p => p.challenge || p.solution).map((pair, i) => (
          <div
            key={i}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: `${s.pairInnerGap}px`,
            }}
          >
            <div
              style={{
                backgroundColor: '#fef2f2',
                borderRadius: `${s.cardBorderRadius}px`,
                borderLeft: `${s.cardBorderLeft}px solid #dc2626`,
                padding: `${s.cardPaddingV}px ${s.cardPaddingH}px`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: `${s.labelMarginBottom}px` }}>
                <AlertTriangle size={s.iconInnerSize * scale} color="#dc2626" />
                <span
                  style={{
                    fontSize: `${s.labelFontSize * scale}px`,
                    fontWeight: 700,
                    letterSpacing: `${s.labelLetterSpacing}px`,
                    textTransform: 'uppercase',
                    color: '#dc2626',
                  }}
                >
                  CHALLENGE
                </span>
              </div>
              <p
                style={{
                  fontSize: `${s.bodyFontSize * scale}px`,
                  color: '#334155',
                  margin: 0,
                  lineHeight: 1.4,
                }}
              >
                {pair.challenge}
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#f0fdf4',
                borderRadius: `${s.cardBorderRadius}px`,
                borderLeft: `${s.cardBorderLeft}px solid #16a34a`,
                padding: `${s.cardPaddingV}px ${s.cardPaddingH}px`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: `${s.labelMarginBottom}px` }}>
                <CheckCircle size={s.iconInnerSize * scale} color="#16a34a" />
                <span
                  style={{
                    fontSize: `${s.labelFontSize * scale}px`,
                    fontWeight: 700,
                    letterSpacing: `${s.labelLetterSpacing}px`,
                    textTransform: 'uppercase',
                    color: '#16a34a',
                  }}
                >
                  SOLUTION
                </span>
              </div>
              <p
                style={{
                  fontSize: `${s.bodyFontSize * scale}px`,
                  color: '#334155',
                  margin: 0,
                  lineHeight: 1.4,
                }}
              >
                {pair.solution}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
