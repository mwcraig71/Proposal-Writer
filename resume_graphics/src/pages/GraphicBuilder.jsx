import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toPng } from 'html-to-image';
import { Plus, Minus, Download, Save, RotateCcw, Sparkles, X } from 'lucide-react';
import { api } from '../lib/api';
import { SIZE_PRESETS, STARTER_SCENARIOS } from '../lib/constants';
import GraphicPreview from '../components/GraphicPreview';
import PreviewControls from '../components/PreviewControls';
import QuickPickSection from '../components/QuickPickSection';

export default function GraphicBuilder() {
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');
  const previewRef = useRef(null);

  const [title, setTitle] = useState('CHALLENGE / SOLUTION');
  const [pairs, setPairs] = useState([
    { challenge: '', solution: '' },
    { challenge: '', solution: '' },
  ]);
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
  const [projects, setProjects] = useState([]);
  const [aiDescription, setAiDescription] = useState('');
  const [aiDirection, setAiDirection] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [graphicName, setGraphicName] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  useEffect(() => {
    loadProjects();
    if (editId) loadGraphic(editId);
  }, [editId]);

  async function loadProjects() {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (e) { /* ignore */ }
  }

  async function loadGraphic(id) {
    try {
      const g = await api.getGraphic(id);
      setTitle(g.data?.title || 'CHALLENGE / SOLUTION');
      setPairs(g.data?.pairs || [{ challenge: '', solution: '' }]);
      setSizePreset(g.data?.sizePreset || 'medium');
      setWidthOverride(g.data?.widthOverride || SIZE_PRESETS[g.data?.sizePreset || 'medium'].baseWidth);
      setFontScale(g.data?.fontScale || 150);
      setGraphicName(g.name || '');
      if (g.projectId) setSelectedProjectId(g.projectId);
    } catch (e) {
      alert('Failed to load graphic: ' + e.message);
    }
  }

  function updatePair(index, field, value) {
    const updated = [...pairs];
    updated[index] = { ...updated[index], [field]: value };
    setPairs(updated);
  }

  function addPair() {
    if (pairs.length < 4) setPairs([...pairs, { challenge: '', solution: '' }]);
  }

  function removePair() {
    if (pairs.length > 1) setPairs(pairs.slice(0, -1));
  }

  function removePairAt(index) {
    if (pairs.length > 1) setPairs(pairs.filter((_, i) => i !== index));
  }

  function loadQuickPick(item) {
    const payload = item.payload || {};
    if (payload.pairs && payload.pairs.length > 0) {
      setPairs(payload.pairs.map(p => ({ ...p })));
    } else if (item.pairs && item.pairs.length > 0) {
      setPairs(item.pairs.map(p => ({ ...p })));
    }
    if (payload.title || item.name) {
      setTitle(payload.title || item.name);
    }
  }

  async function handleSelectProject(e) {
    const id = e.target.value;
    if (!id) { setSelectedProjectId(null); return; }
    setSelectedProjectId(parseInt(id));
    const proj = projects.find(p => String(p.id) === String(id));
    if (proj) {
      setAiDescription(proj.description || proj.title || '');
    }
  }

  async function handleAiGenerate() {
    if (!aiDescription.trim()) return alert('Please enter a project description.');
    setAiLoading(true);
    try {
      const result = await api.aiParseProject({ projectDescription: aiDescription, direction: aiDirection });
      if (result.pairs) setPairs(result.pairs.slice(0, 4));
      if (result.title) setTitle(result.title);
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
        type: 'challenge_solution',
        data: { title, pairs, sizePreset, widthOverride, fontScale },
        projectId: selectedProjectId || null,
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
    setTitle('CHALLENGE / SOLUTION');
    setPairs([{ challenge: '', solution: '' }, { challenge: '', solution: '' }]);
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
      link.download = `${title || 'graphic'}.png`;
      link.href = dataUrl;
      link.click();
    } catch (e) {
      alert('Download failed: ' + e.message);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Challenge / Solution Builder</h2>
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

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            />
          </div>

          <QuickPickSection
            type="challenge-solution"
            builtInItems={STARTER_SCENARIOS.map(sc => ({ name: sc.name, payload: { title: sc.name, pairs: sc.pairs } }))}
            onSelect={loadQuickPick}
            currentData={() => ({ title, pairs })}
            currentName={graphicName}
          />

          {pairs.map((pair, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-lg p-4 relative group">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold text-slate-500 uppercase">Pair {i + 1}</h4>
                {pairs.length > 1 && (
                  <button onClick={() => removePairAt(i)} className="text-slate-300 hover:text-red-500 transition" title="Delete this pair">
                    <X size={16} />
                  </button>
                )}
              </div>
              <div className="space-y-2">
                <div>
                  <label className="block text-xs font-medium text-red-600 mb-1">Challenge</label>
                  <textarea
                    value={pair.challenge}
                    onChange={(e) => updatePair(i, 'challenge', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-sm resize-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-green-600 mb-1">Solution</label>
                  <textarea
                    value={pair.solution}
                    onChange={(e) => updatePair(i, 'solution', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-slate-300 rounded text-sm resize-none"
                  />
                </div>
              </div>
            </div>
          ))}

          <div className="flex gap-2">
            <button onClick={addPair} disabled={pairs.length >= 4} className="flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-40">
              <Plus size={14} /> Add Pair
            </button>
            <button onClick={removePair} disabled={pairs.length <= 1} className="flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-40">
              <Minus size={14} /> Remove Pair
            </button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
              <Sparkles size={16} /> AI Project Assistant
            </h3>
            <div className="space-y-2">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Select Project</label>
                <select value={selectedProjectId || ''} onChange={handleSelectProject} className="w-full px-3 py-2 border border-slate-300 rounded text-sm bg-white">
                  <option value="">-- Select a project --</option>
                  {projects.map(p => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Project Description</label>
                <textarea
                  value={aiDescription}
                  onChange={(e) => setAiDescription(e.target.value)}
                  rows={3}
                  placeholder="Describe the project..."
                  className="w-full px-3 py-2 border border-slate-300 rounded text-sm resize-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Direction (optional)</label>
                <input
                  type="text"
                  value={aiDirection}
                  onChange={(e) => setAiDirection(e.target.value)}
                  placeholder="e.g., Focus on safety challenges"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-sm"
                />
              </div>
              <button
                onClick={handleAiGenerate}
                disabled={aiLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
              >
                <Sparkles size={14} /> {aiLoading ? 'Generating...' : 'Generate Pairs'}
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
            <GraphicPreview
              pairs={pairs}
              title={title}
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
