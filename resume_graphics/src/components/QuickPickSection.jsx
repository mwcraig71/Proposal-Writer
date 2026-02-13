import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Plus, Pencil, Trash2, Check, X, Save } from 'lucide-react';
import { api } from '../lib/api';

export default function QuickPickSection({ type, builtInItems, onSelect, currentData, currentName }) {
  const [items, setItems] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadItems();
  }, [type]);

  async function loadItems() {
    try {
      const data = await api.getScenarios(type);
      setItems(data);
    } catch (e) { /* ignore */ }
  }

  async function handleSaveCurrentAsQuickPick() {
    const name = prompt('Name this quick pick:');
    if (!name) return;
    setSaving(true);
    try {
      await api.createScenario({
        name,
        type,
        payload: currentData(),
      });
      await loadItems();
    } catch (e) {
      alert('Failed to save: ' + e.message);
    }
    setSaving(false);
  }

  async function handleDelete(id) {
    if (!confirm('Delete this quick pick?')) return;
    try {
      await api.deleteScenario(id);
      setItems(items.filter(i => i.id !== id));
    } catch (e) {
      alert('Failed to delete: ' + e.message);
    }
  }

  async function handleEditSave(id) {
    if (!editName.trim()) return;
    try {
      await api.updateScenario(id, { name: editName.trim() });
      setItems(items.map(i => i.id === id ? { ...i, name: editName.trim() } : i));
      setEditingId(null);
    } catch (e) {
      alert('Failed to update: ' + e.message);
    }
  }

  function handleSelect(item) {
    onSelect(item);
  }

  const visibleCount = 6;
  const allItems = [
    ...(builtInItems || []).map((b, i) => ({ ...b, _builtIn: true, _key: `b-${i}` })),
    ...items.map(i => ({ ...i, _builtIn: false, _key: `s-${i.id}` })),
  ];
  const showExpand = allItems.length > visibleCount;
  const displayItems = expanded ? allItems : allItems.slice(0, visibleCount);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-700">Quick Picks</h3>
        <button
          onClick={handleSaveCurrentAsQuickPick}
          disabled={saving}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-50 text-amber-700 rounded hover:bg-amber-100 border border-amber-200 transition disabled:opacity-50"
          title="Save current settings as a quick pick"
        >
          <Save size={12} />
          {saving ? 'Saving...' : 'Save Current'}
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {displayItems.map((item) => (
          <div key={item._key} className="group relative flex items-center">
            {editingId === item.id ? (
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleEditSave(item.id)}
                  className="px-2 py-1 text-xs border border-blue-300 rounded w-32 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  autoFocus
                />
                <button onClick={() => handleEditSave(item.id)} className="text-green-600 hover:text-green-800">
                  <Check size={14} />
                </button>
                <button onClick={() => setEditingId(null)} className="text-slate-400 hover:text-slate-600">
                  <X size={14} />
                </button>
              </div>
            ) : (
              <div className="flex items-center">
                <button
                  onClick={() => handleSelect(item)}
                  className={`px-3 py-1.5 text-xs rounded-l-full font-medium transition ${
                    item._builtIn
                      ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                  }`}
                >
                  {item.name}
                </button>
                {!item._builtIn && (
                  <div className="flex opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={(e) => { e.stopPropagation(); setEditingId(item.id); setEditName(item.name); }}
                      className="px-1 py-1.5 text-xs bg-slate-100 text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition"
                      title="Rename"
                    >
                      <Pencil size={11} />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
                      className="px-1 py-1.5 text-xs bg-slate-100 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-r-full transition"
                      title="Delete"
                    >
                      <Trash2 size={11} />
                    </button>
                  </div>
                )}
                {item._builtIn && (
                  <span className="w-0" />
                )}
                {(item._builtIn || (!item._builtIn && editingId !== item.id)) && (
                  <span className={`rounded-r-full ${item._builtIn ? '' : 'group-hover:hidden'} w-0`} />
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      {showExpand && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 transition"
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {expanded ? 'Show less' : `Show ${allItems.length - visibleCount} more`}
        </button>
      )}
    </div>
  );
}
