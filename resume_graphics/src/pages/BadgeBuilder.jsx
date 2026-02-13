import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toPng } from 'html-to-image';
import { Plus, Minus, Download, Save, RotateCcw, Sparkles } from 'lucide-react';
import { api } from '../lib/api';
import { SIZE_PRESETS, DEFAULT_BADGES, ICON_OPTIONS } from '../lib/constants';
import BadgePreview from '../components/BadgePreview';
import PreviewControls from '../components/PreviewControls';

export default function BadgeBuilder() {
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');
  const previewRef = useRef(null);

  const [badges, setBadges] = useState(DEFAULT_BADGES.map(b => ({ ...b })));
  const [sizePreset, setSizePreset] = useState('medium');
  const [widthOverride, setWidthOverride] = useState(SIZE_PRESETS.medium.baseWidth);
  const [fontScale, setFontScale] = useState(() => {
    const saved = localStorage.getItem('resumeGraphicFontScale');
    return saved ? parseInt(saved, 10) : 150;
  });
  const handleFontScaleChange = (val) => {
    setFontScale(val);
    localStorage.setItem('resumeGraphicFontScale', val);
  };
  const [saving, setSaving] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [aiResumeText, setAiResumeText] = useState('');
  const [aiFocus, setAiFocus] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [graphicName, setGraphicName] = useState('');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);

  useEffect(() => {
    loadEmployees();
    if (editId) loadGraphic(editId);
  }, [editId]);

  async function loadEmployees() {
    try {
      const data = await api.getEmployees();
      setEmployees(data);
    } catch (e) { /* ignore */ }
  }

  async function loadGraphic(id) {
    try {
      const g = await api.getGraphic(id);
      setBadges(g.data?.badges || DEFAULT_BADGES.map(b => ({ ...b })));
      setSizePreset(g.data?.sizePreset || 'medium');
      setWidthOverride(g.data?.widthOverride || SIZE_PRESETS[g.data?.sizePreset || 'medium'].baseWidth);
      setFontScale(g.data?.fontScale || 150);
      setGraphicName(g.name || '');
      if (g.employeeId) setSelectedEmployeeId(g.employeeId);
    } catch (e) {
      alert('Failed to load graphic: ' + e.message);
    }
  }

  function updateBadge(index, field, value) {
    const updated = [...badges];
    updated[index] = { ...updated[index], [field]: value };
    setBadges(updated);
  }

  function addBadge() {
    if (badges.length < 8) setBadges([...badges, { label: '', value: '', icon: 'Shield' }]);
  }

  function removeBadge() {
    if (badges.length > 1) setBadges(badges.slice(0, -1));
  }

  async function handleSelectEmployee(e) {
    const id = e.target.value;
    if (!id) { setSelectedEmployeeId(null); return; }
    setSelectedEmployeeId(parseInt(id));
    const emp = employees.find(p => String(p.id) === String(id));
    if (emp) {
      const parts = [emp.bio, emp.education, emp.registrations].filter(Boolean);
      setAiResumeText(parts.join('\n\n') || emp.name || '');
    }
  }

  async function handleAiGenerate() {
    if (!aiResumeText.trim()) return alert('Please enter resume text.');
    setAiLoading(true);
    try {
      const result = await api.aiParseResume({ resumeText: aiResumeText, focusAreas: aiFocus });
      if (result.badges) setBadges(result.badges.slice(0, 8));
    } catch (e) {
      alert('AI generation failed: ' + e.message);
    } finally {
      setAiLoading(false);
    }
  }

  async function handleSave() {
    const name = graphicName || prompt('Name this graphic:');
    if (!name) return;
    setGraphicName(name);
    setSaving(true);
    try {
      const payload = {
        name,
        type: 'badge',
        data: { badges, sizePreset, widthOverride, fontScale },
        employeeId: selectedEmployeeId || null,
      };
      let graphicId = editId;
      if (editId) {
        await api.updateGraphic(editId, payload);
      } else {
        const result = await api.createGraphic(payload);
        graphicId = result.id;
      }
      if (previewRef.current && graphicId) {
        try {
          const dataUrl = await toPng(previewRef.current, { pixelRatio: 3 });
          await api.uploadSnapshot(graphicId, dataUrl);
        } catch (snapErr) {
          console.warn('Snapshot upload failed:', snapErr);
        }
      }
      alert('Saved!');
    } catch (e) {
      alert('Save failed: ' + e.message);
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setBadges(DEFAULT_BADGES.map(b => ({ ...b })));
    setSizePreset('medium');
    setWidthOverride(SIZE_PRESETS.medium.baseWidth);
    handleFontScaleChange(150);
    setGraphicName('');
  }

  async function handleDownload() {
    if (!previewRef.current) return;
    try {
      const dataUrl = await toPng(previewRef.current, { pixelRatio: 3 });
      const link = document.createElement('a');
      link.download = `badges-${graphicName || 'graphic'}.png`;
      link.href = dataUrl;
      link.click();
    } catch (e) {
      alert('Download failed: ' + e.message);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Badge Builder</h2>
        <div className="flex gap-2">
          <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-[#cf3910] text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm font-medium">
            <Save size={16} /> Save
          </button>
          <button onClick={handleReset} className="flex items-center gap-2 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 text-sm font-medium">
            <RotateCcw size={16} /> Reset
          </button>
          <button onClick={handleDownload} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium">
            <Download size={16} /> Download PNG
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Graphic Name</label>
            <input
              type="text"
              value={graphicName}
              onChange={(e) => setGraphicName(e.target.value)}
              placeholder="Name for saving..."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>

          {badges.map((badge, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">Badge {i + 1}</h4>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Icon</label>
                  <select
                    value={badge.icon}
                    onChange={(e) => updateBadge(i, 'icon', e.target.value)}
                    className="w-full px-2 py-2 border border-slate-300 rounded text-sm bg-white"
                  >
                    {ICON_OPTIONS.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Label</label>
                  <input
                    type="text"
                    value={badge.label}
                    onChange={(e) => updateBadge(i, 'label', e.target.value)}
                    className="w-full px-2 py-2 border border-slate-300 rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Value</label>
                  <input
                    type="text"
                    value={badge.value}
                    onChange={(e) => updateBadge(i, 'value', e.target.value)}
                    className="w-full px-2 py-2 border border-slate-300 rounded text-sm"
                  />
                </div>
              </div>
            </div>
          ))}

          <div className="flex gap-2">
            <button onClick={addBadge} disabled={badges.length >= 8} className="flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-40">
              <Plus size={14} /> Add Badge
            </button>
            <button onClick={removeBadge} disabled={badges.length <= 1} className="flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-40">
              <Minus size={14} /> Remove Badge
            </button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
              <Sparkles size={16} /> AI Resume Parser
            </h3>
            <div className="space-y-2">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Select Employee</label>
                <select value={selectedEmployeeId || ''} onChange={handleSelectEmployee} className="w-full px-3 py-2 border border-slate-300 rounded text-sm bg-white">
                  <option value="">-- Select an employee --</option>
                  {employees.map(e => (
                    <option key={e.id} value={e.id}>{e.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Resume Text</label>
                <textarea
                  value={aiResumeText}
                  onChange={(e) => setAiResumeText(e.target.value)}
                  rows={4}
                  placeholder="Paste resume content..."
                  className="w-full px-3 py-2 border border-slate-300 rounded text-sm resize-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Focus Areas (optional)</label>
                <input
                  type="text"
                  value={aiFocus}
                  onChange={(e) => setAiFocus(e.target.value)}
                  placeholder="e.g., bridge inspection, NDT"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-sm"
                />
              </div>
              <button
                onClick={handleAiGenerate}
                disabled={aiLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
              >
                <Sparkles size={14} /> {aiLoading ? 'Parsing...' : 'Generate Badges'}
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <PreviewControls
            sizePreset={sizePreset}
            setSizePreset={setSizePreset}
            widthOverride={widthOverride}
            setWidthOverride={setWidthOverride}
            fontScale={fontScale}
            setFontScale={handleFontScaleChange}
          />
          <div className="bg-slate-200 rounded-lg p-4 overflow-auto">
            <BadgePreview
              badges={badges}
              sizePreset={sizePreset}
              widthOverride={widthOverride}
              fontScale={fontScale}
              previewRef={previewRef}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
