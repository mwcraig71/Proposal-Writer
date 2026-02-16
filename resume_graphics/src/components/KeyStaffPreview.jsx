import React from 'react';
import { Key, Check } from 'lucide-react';
import { SIZE_PRESETS } from '../lib/constants';
import { getIcon } from '../lib/icons';

export default function KeyStaffPreview({ staff, title, columns, sizePreset, widthOverride, fontScale, previewRef }) {
  const s = SIZE_PRESETS[sizePreset] || SIZE_PRESETS.medium;
  const scale = (fontScale || 100) / 100;
  const width = widthOverride || s.baseWidth;
  const cols = columns || 2;

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
          {title || 'KEY STAFF'}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gap: `${s.pairGap}px`,
        }}
      >
        {(staff || []).filter(s => s.name).map((member, i) => {
          const IconComp = member.icon ? getIcon(member.icon) : (i === 0 ? Key : Check);
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: `${s.cardPaddingV}px ${s.cardPaddingH}px`,
                borderLeft: `${s.cardBorderLeft}px solid #cf3910`,
                borderRadius: `${s.cardBorderRadius}px`,
                backgroundColor: '#fafafa',
              }}
            >
              <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                <IconComp size={s.iconInnerSize * scale} color="#cf3910" />
              </span>
              <span
                style={{
                  fontSize: `${s.bodyFontSize * scale}px`,
                  color: '#334155',
                  fontWeight: 500,
                }}
              >
                {member.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
