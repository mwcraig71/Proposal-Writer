import React from 'react';
import { SIZE_PRESETS } from '../lib/constants';
import { getIcon } from '../lib/icons';

export default function BadgePreview({ badges, sizePreset, widthOverride, fontScale, previewRef }) {
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
          paddingLeft: '8px',
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
          TECHNICAL COMPETENCIES
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: `${s.badgeGap}px` }}>
        {(badges || []).filter(b => b.label || b.value).map((badge, i) => {
          const IconComp = getIcon(badge.icon);
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                borderLeft: `${s.cardBorderLeft}px solid #cf3910`,
                borderRadius: `${s.cardBorderRadius}px`,
                backgroundColor: '#fff',
                padding: `${s.badgePaddingV}px ${s.badgePaddingH}px`,
              }}
            >
              <div
                style={{
                  width: `${s.badgeIconBoxSize * scale}px`,
                  height: `${s.badgeIconBoxSize * scale}px`,
                  borderRadius: `${s.badgeIconBoxRadius}px`,
                  backgroundColor: '#fef2f2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <IconComp size={s.badgeIconSize * scale} color="#cf3910" />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span
                  style={{
                    fontSize: `${s.badgeLabelFontSize * scale}px`,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.8px',
                    color: '#cf3910',
                  }}
                >
                  {badge.label}
                </span>
                <span
                  style={{
                    fontSize: `${s.badgeValueFontSize * scale}px`,
                    color: '#334155',
                    fontWeight: 500,
                  }}
                >
                  {badge.value}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
