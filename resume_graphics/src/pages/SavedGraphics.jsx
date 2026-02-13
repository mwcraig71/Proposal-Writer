import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toPng } from 'html-to-image';
import { Edit, Eye, EyeOff, Download, Trash2, Loader2, User, FolderOpen } from 'lucide-react';
import { api } from '../lib/api';
import { SIZE_PRESETS, DEFAULT_BADGES, DEFAULT_STAFF } from '../lib/constants';
import GraphicPreview from '../components/GraphicPreview';
import BadgePreview from '../components/BadgePreview';
import KeyStaffPreview from '../components/KeyStaffPreview';

function TypeBadge({ type }) {
  const colors = {
    challenge_solution: 'bg-red-100 text-red-700',
    badge: 'bg-purple-100 text-purple-700',
    key_staff: 'bg-blue-100 text-blue-700',
  };
  const labels = {
    challenge_solution: 'Challenge/Solution',
    badge: 'Badge',
    key_staff: 'Key Staff',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[type] || 'bg-slate-100 text-slate-600'}`}>
      {labels[type] || type}
    </span>
  );
}

function InlinePreview({ graphic }) {
  const ref = useRef(null);
  const data = graphic.data || {};
  const sizePreset = data.sizePreset || 'medium';
  const widthOverride = data.widthOverride || SIZE_PRESETS[sizePreset]?.baseWidth || 500;
  const fontScale = data.fontScale || 100;

  if (graphic.type === 'challenge_solution') {
    return (
      <GraphicPreview
        pairs={data.pairs || []}
        title={data.title || 'CHALLENGE / SOLUTION'}
        sizePreset={sizePreset}
        widthOverride={widthOverride}
        fontScale={fontScale}
        previewRef={ref}
      />
    );
  }
  if (graphic.type === 'badge') {
    return (
      <BadgePreview
        badges={data.badges || DEFAULT_BADGES}
        sizePreset={sizePreset}
        widthOverride={widthOverride}
        fontScale={fontScale}
        previewRef={ref}
      />
    );
  }
  if (graphic.type === 'key_staff') {
    return (
      <KeyStaffPreview
        staff={data.staff || DEFAULT_STAFF}
        title={data.title || 'KEY STAFF'}
        columns={data.columns || 2}
        sizePreset={sizePreset}
        widthOverride={widthOverride}
        fontScale={fontScale}
        previewRef={ref}
      />
    );
  }
  return <div className="text-sm text-slate-500">Unknown type</div>;
}

function DownloadablePreview({ graphic }) {
  const ref = useRef(null);
  const data = graphic.data || {};
  const sizePreset = data.sizePreset || 'medium';
  const widthOverride = data.widthOverride || SIZE_PRESETS[sizePreset]?.baseWidth || 500;
  const fontScale = data.fontScale || 100;

  async function handleDownload() {
    if (!ref.current) return;
    try {
      const dataUrl = await toPng(ref.current, { pixelRatio: 3 });
      const link = document.createElement('a');
      link.download = `${graphic.name || 'graphic'}.png`;
      link.href = dataUrl;
      link.click();
    } catch (e) {
      alert('Download failed: ' + e.message);
    }
  }

  const previewProps = { sizePreset, widthOverride, fontScale, previewRef: ref };

  return {
    handleDownload,
    element: (
      <div style={{ position: 'absolute', left: '-9999px', top: 0 }}>
        {graphic.type === 'challenge_solution' && (
          <GraphicPreview pairs={data.pairs || []} title={data.title || ''} {...previewProps} />
        )}
        {graphic.type === 'badge' && (
          <BadgePreview badges={data.badges || []} {...previewProps} />
        )}
        {graphic.type === 'key_staff' && (
          <KeyStaffPreview staff={data.staff || []} title={data.title || 'KEY STAFF'} columns={data.columns || 2} {...previewProps} />
        )}
      </div>
    ),
  };
}

function GraphicRow({ graphic, onDelete, onEdit }) {
  const [expanded, setExpanded] = useState(false);
  const downloadRef = useRef(null);

  const downloadHelper = DownloadablePreview({ graphic });

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      {downloadHelper.element}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <div>
            <h3 className="font-semibold text-slate-800">{graphic.name}</h3>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <TypeBadge type={graphic.type} />
              {graphic.employeeName && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                  <User size={10} /> {graphic.employeeName}
                </span>
              )}
              {graphic.projectName && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700">
                  <FolderOpen size={10} /> {graphic.projectName}
                </span>
              )}
              <span className="text-xs text-slate-400">
                {graphic.created_at ? new Date(graphic.created_at).toLocaleDateString() : ''}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onEdit(graphic)}
            className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Edit"
          >
            <Edit size={16} />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 text-slate-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            title="Preview"
          >
            {expanded ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
          <button
            onClick={downloadHelper.handleDownload}
            className="p-2 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
            title="Download PNG"
          >
            <Download size={16} />
          </button>
          <button
            onClick={() => onDelete(graphic.id)}
            className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
      {expanded && (
        <div className="border-t border-slate-200 p-4 bg-slate-50 overflow-auto">
          <InlinePreview graphic={graphic} />
        </div>
      )}
    </div>
  );
}

export default function SavedGraphics() {
  const [graphics, setGraphics] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadGraphics();
  }, []);

  async function loadGraphics() {
    setLoading(true);
    try {
      const data = await api.getGraphics();
      setGraphics(Array.isArray(data) ? data : []);
    } catch (e) {
      alert('Failed to load graphics: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this graphic?')) return;
    try {
      await api.deleteGraphic(id);
      setGraphics(graphics.filter(g => g.id !== id));
    } catch (e) {
      alert('Delete failed: ' + e.message);
    }
  }

  function handleEdit(graphic) {
    const routes = {
      challenge_solution: '/',
      badge: '/badges',
      key_staff: '/key-staff',
    };
    const route = routes[graphic.type] || '/';
    navigate(`${route}?edit=${graphic.id}`);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-slate-400" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Saved Graphics</h2>
        <span className="text-sm text-slate-500">{graphics.length} graphic{graphics.length !== 1 ? 's' : ''}</span>
      </div>

      {graphics.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <p className="text-lg font-medium">No saved graphics yet</p>
          <p className="text-sm mt-1">Create a graphic and save it to see it here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {graphics.map(g => (
            <GraphicRow
              key={g.id}
              graphic={g}
              onDelete={handleDelete}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}
    </div>
  );
}
