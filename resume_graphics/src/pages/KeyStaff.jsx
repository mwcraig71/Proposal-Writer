import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toPng } from 'html-to-image';
import { Plus, Minus, Download, Save, RotateCcw, X } from 'lucide-react';
import { api } from '../lib/api';
import { SIZE_PRESETS, DEFAULT_STAFF, ICON_OPTIONS } from '../lib/constants';
import KeyStaffPreview from '../components/KeyStaffPreview';
import PreviewControls from '../components/PreviewControls';
import QuickPickSection from '../components/QuickPickSection';

function firstLastName(fullName) {
  if (!fullName) return '';
  const parts = fullName.trim().split(/\s+/);
  if (parts.length <= 2) return parts.join(' ');
  return `${parts[0]} ${parts[parts.length - 1]}`;
}

export default function KeyStaff() {
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');
  const previewRef = useRef(null);

  const [title, setTitle] = useState('KEY STAFF');
  const [columns, setColumns] = useState(2);
  const [staff, setStaff] = useState(DEFAULT_STAFF.map(s => ({ ...s })));
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
  const [graphicName, setGraphicName] = useState('');

  const [firms, setFirms] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedFirmId, setSelectedFirmId] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        const [firmsData, employeesData, projectsData] = await Promise.all([
          api.getFirms(),
          api.getEmployees(),
          api.getProjects(),
        ]);
        setFirms(firmsData);
        setEmployees(employeesData);
        setProjects(projectsData);
      } catch (e) {
        console.error('Failed to load data:', e);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    if (editId) loadGraphic(editId);
  }, [editId]);

  async function loadGraphic(id) {
    try {
      const g = await api.getGraphic(id);
      setTitle(g.data?.title || 'KEY STAFF');
      setColumns(g.data?.columns || 2);
      setStaff(g.data?.staff || DEFAULT_STAFF.map(s => ({ ...s })));
      setSizePreset(g.data?.sizePreset || 'medium');
      setWidthOverride(g.data?.widthOverride || SIZE_PRESETS[g.data?.sizePreset || 'medium'].baseWidth);
      setFontScale(g.data?.fontScale || 150);
      setGraphicName(g.name || '');
    } catch (e) {
      alert('Failed to load graphic: ' + e.message);
    }
  }

  function updateStaff(index, field, value) {
    const updated = [...staff];
    updated[index] = { ...updated[index], [field]: value };
    setStaff(updated);
  }

  function addStaff() {
    if (staff.length < 20) setStaff([...staff, { name: '', icon: 'Check' }]);
  }

  function removeStaff() {
    if (staff.length > 1) setStaff(staff.slice(0, -1));
  }

  function removeStaffAt(index) {
    if (staff.length > 1) setStaff(staff.filter((_, i) => i !== index));
  }

  function loadQuickPick(item) {
    const payload = item.payload || {};
    if (payload.staff && payload.staff.length > 0) {
      setStaff(payload.staff.map(s => ({ ...s })));
    }
    if (payload.title) setTitle(payload.title);
    if (payload.columns) setColumns(payload.columns);
  }

  const filteredProjects = selectedFirmId
    ? projects.filter(p => String(p.firmId) === String(selectedFirmId))
    : projects;

  function handleFirmSelect(firmId) {
    setSelectedFirmId(firmId);
    setSelectedProjectId('');
    if (!firmId) return;
    const firmEmployees = employees.filter(e => String(e.firmId) === String(firmId));
    if (firmEmployees.length > 0) {
      setStaff(firmEmployees.map(e => ({
        name: `${firstLastName(e.name)}, ${e.role || ''}`.replace(/, $/, ''),
        icon: 'Check',
      })));
    }
  }

  async function handleProjectSelect(projectId) {
    setSelectedProjectId(projectId);
    if (!projectId) return;
    try {
      const personnel = await api.getProjectPersonnel(projectId);
      if (personnel.length > 0) {
        setStaff(personnel.map(p => ({
          name: `${firstLastName(p.name)}, ${p.role || ''}`.replace(/, $/, ''),
          icon: 'Check',
        })));
      }
    } catch (e) {
      console.error('Failed to load project personnel:', e);
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
        type: 'key_staff',
        data: { title, columns, staff, sizePreset, widthOverride, fontScale },
      };
      if (selectedProjectId) {
        payload.projectId = parseInt(selectedProjectId);
      }
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
    setTitle('KEY STAFF');
    setColumns(2);
    setStaff(DEFAULT_STAFF.map(s => ({ ...s })));
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
      link.download = `${title || 'key-staff'}.png`;
      link.href = dataUrl;
      link.click();
    } catch (e) {
      alert('Download failed: ' + e.message);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Key Staff Builder</h2>
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Columns</label>
              <select
                value={columns}
                onChange={(e) => setColumns(Number(e.target.value))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                {[1, 2, 3, 4].map(n => (
                  <option key={n} value={n}>{n} Column{n > 1 ? 's' : ''}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Firm</label>
              <select
                value={selectedFirmId}
                onChange={(e) => handleFirmSelect(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="">— Select Firm —</option>
                {firms.map(f => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Project</label>
              <select
                value={selectedProjectId}
                onChange={(e) => handleProjectSelect(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="">— Select Project —</option>
                {filteredProjects.map(p => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
            </div>
          </div>

          <QuickPickSection
            type="key-staff"
            onSelect={loadQuickPick}
            currentData={() => ({ title, columns, staff })}
            currentName={graphicName}
          />

          {staff.map((member, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-400 w-6">{i + 1}.</span>
                <select
                  value={member.icon}
                  onChange={(e) => updateStaff(i, 'icon', e.target.value)}
                  className="w-28 px-2 py-1.5 border border-slate-300 rounded text-sm bg-white"
                >
                  {ICON_OPTIONS.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={member.name}
                  onChange={(e) => updateStaff(i, 'name', e.target.value)}
                  placeholder="Staff name, title"
                  className="flex-1 px-2 py-1.5 border border-slate-300 rounded text-sm"
                />
                {staff.length > 1 && (
                  <button onClick={() => removeStaffAt(i)} className="text-slate-300 hover:text-red-500 transition" title="Delete this staff member">
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}

          <div className="flex gap-2">
            <button onClick={addStaff} disabled={staff.length >= 20} className="flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-40">
              <Plus size={14} /> Add Staff
            </button>
            <button onClick={removeStaff} disabled={staff.length <= 1} className="flex items-center gap-1 px-3 py-1.5 text-sm bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-40">
              <Minus size={14} /> Remove Staff
            </button>
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
            <KeyStaffPreview
              staff={staff}
              title={title}
              columns={columns}
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
