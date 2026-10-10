/**
 * Normal Editor - Personal Code Workspace Engine
 * Supports multi-language editing, file explorer, autosave, manual save,
 * version history management, upload/download, and workspace persistence.
 */

(function () {
  'use strict';

  // Global state
  let editor = null;
  let activeFileId = null;
  let activeFileName = '';
  let activeLanguage = 'plaintext';
  let isDirty = false;
  let isSaving = false;
  let autosaveTimer = null;
  let currentTheme = 'vs-dark';
  let currentFontSize = 14;

  // DOM Elements
  const container = document.getElementById('normalEditorContainer');
  const textareaFallback = document.getElementById('normalFallbackTextarea');
  const saveBtn = document.getElementById('btnManualSave');
  const downloadBtn = document.getElementById('btnDownloadCurrent');
  const newFileBtn = document.getElementById('btnNewFileModal');
  const uploadFileInput = document.getElementById('uploadFileInput');
  const themeSelect = document.getElementById('normalThemeSelect');
  const fontIncBtn = document.getElementById('btnNormalFontInc');
  const fontDecBtn = document.getElementById('btnNormalFontDec');
  const statusBadge = document.getElementById('normalSaveStatus');
  const activeFileNameEl = document.getElementById('activeFileNameDisplay');
  const activeLangBadge = document.getElementById('activeLangBadge');
  const fileSearchInput = document.getElementById('fileSearchInput');
  const fileListContainer = document.getElementById('fileListContainer');
  const versionsListContainer = document.getElementById('versionsListContainer');

  // Map extensions to Monaco languages
  const EXT_LANG_MAP = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'java': 'java',
    'c': 'c',
    'h': 'c',
    'cpp': 'cpp',
    'hpp': 'cpp',
    'cc': 'cpp',
    'json': 'json',
    'sql': 'sql',
    'md': 'markdown',
    'txt': 'plaintext',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml'
  };

  function getLanguageFromFilename(fname) {
    if (!fname) return 'plaintext';
    const parts = fname.split('.');
    if (parts.length < 2) return 'plaintext';
    const ext = parts[parts.length - 1].toLowerCase();
    return EXT_LANG_MAP[ext] || 'plaintext';
  }

  /**
   * 1. Initialize Monaco Editor
   */
  function initEditor() {
    if (!container) return;

    activeFileId = container.dataset.activeFileId ? parseInt(container.dataset.activeFileId) : null;
    activeFileName = container.dataset.activeFileName || 'untitled.py';
    activeLanguage = getLanguageFromFilename(activeFileName);
    const initialContent = container.dataset.initialContent || '';

    if (window.monaco) {
      editor = monaco.editor.create(container, {
        value: initialContent,
        language: activeLanguage,
        theme: currentTheme,
        fontSize: currentFontSize,
        fontFamily: "'Fira Code', 'Consolas', monospace",
        automaticLayout: true,
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        roundedSelection: true,
        tabSize: 4,
        insertSpaces: true,
        lineNumbers: 'on',
        renderWhitespace: 'selection',
        bracketPairColorization: { enabled: true },
        padding: { top: 12, bottom: 12 }
      });

      // Track typing for debounce auto-save & dirty status
      editor.onDidChangeModelContent(function () {
        setDirty(true);
        triggerAutosave();
      });

      // Keyboard Shortcuts
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, function () {
        handleSave(true, 'Manual save');
      });

      if (textareaFallback) textareaFallback.style.display = 'none';
    } else if (textareaFallback) {
      textareaFallback.style.display = 'block';
      textareaFallback.value = initialContent;
      textareaFallback.addEventListener('input', function () {
        setDirty(true);
        triggerAutosave();
      });
    }

    updateUIHeader();
    setupEventListeners();
  }

  function getContent() {
    if (editor) return editor.getValue();
    if (textareaFallback) return textareaFallback.value;
    return '';
  }

  function setContent(text, filename) {
    activeFileName = filename || activeFileName;
    activeLanguage = getLanguageFromFilename(activeFileName);

    if (editor && window.monaco) {
      const model = editor.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, activeLanguage);
      }
      editor.setValue(text || '');
    } else if (textareaFallback) {
      textareaFallback.value = text || '';
    }

    setDirty(false);
    updateUIHeader();
  }

  function setDirty(dirty) {
    isDirty = dirty;
    if (statusBadge) {
      if (dirty) {
        statusBadge.innerHTML = '<span style="color: #fb923c;">● Unsaved changes</span>';
      } else {
        statusBadge.innerHTML = '<span style="color: #22c55e;">● Saved</span>';
      }
    }
  }

  function updateUIHeader() {
    if (activeFileNameEl) activeFileNameEl.textContent = activeFileName;
    if (activeLangBadge) {
      activeLangBadge.textContent = activeLanguage.toUpperCase();
    }
  }

  /**
   * 2. Auto-Save with 2-second debounce
   */
  function triggerAutosave() {
    if (autosaveTimer) clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(function () {
      if (isDirty && activeFileId) {
        handleSave(false, 'Auto-saved changes');
      }
    }, 2000);
  }

  /**
   * 3. Save File API Call
   */
  async function handleSave(manual = false, summary = 'Saved changes') {
    if (!activeFileId || isSaving) return;

    isSaving = true;
    if (statusBadge) {
      statusBadge.innerHTML = '<span style="color: #38bdf8;">⏳ Saving...</span>';
    }

    const content = getContent();

    try {
      const response = await fetch(`/api/student/files/${activeFileId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: content,
          summary: summary,
          create_version: manual // Create new version snapshot on manual save
        })
      });

      const data = await response.json();
      if (data.success) {
        setDirty(false);
        if (manual) {
          loadVersionsList(activeFileId);
        }
      } else {
        if (statusBadge) {
          statusBadge.innerHTML = `<span style="color: #ef4444;" title="${data.error || 'Save failed'}">⚠️ Save failed (Retry)</span>`;
        }
      }
    } catch (err) {
      if (statusBadge) {
        statusBadge.innerHTML = '<span style="color: #ef4444;">⚠️ Network error</span>';
      }
    } finally {
      isSaving = false;
    }
  }

  /**
   * 4. Open File in Editor
   */
  window.openStudentFile = async function (fileId) {
    if (isDirty) {
      await handleSave(false, 'Auto-saved before switching file');
    }

    try {
      const response = await fetch(`/api/student/files/${fileId}`);
      const data = await response.json();
      if (data.success) {
        activeFileId = data.file.id;
        setContent(data.file.content, data.file.filename);

        // Highlight active item in sidebar
        document.querySelectorAll('.file-tree-item').forEach(el => el.classList.remove('active'));
        const activeItem = document.querySelector(`.file-tree-item[data-file-id="${fileId}"]`);
        if (activeItem) activeItem.classList.add('active');

        // Update URL state without page reload
        window.history.pushState({}, '', `/student/editor/${fileId}`);

        // Render versions
        renderVersions(data.versions || []);
      }
    } catch (e) {
      console.error('Failed to open file:', e);
    }
  };

  /**
   * 5. Load & Render Versions
   */
  async function loadVersionsList(fileId) {
    if (!fileId) return;
    try {
      const res = await fetch(`/api/student/files/${fileId}/versions`);
      const data = await res.json();
      if (data.success) {
        renderVersions(data.versions || []);
      }
    } catch (e) {
      console.warn('Failed to load versions:', e);
    }
  }

  function renderVersions(versions) {
    if (!versionsListContainer) return;
    if (!versions || versions.length === 0) {
      versionsListContainer.innerHTML = '<div style="padding: 0.75rem; color: #8b949e; font-size: 0.8rem;">No version history yet.</div>';
      return;
    }

    let html = '';
    versions.forEach(function (v) {
      html += `
        <div class="version-item" style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem;">
          <div>
            <div style="font-weight: 600; color: #f0f6fc;">v${v.version_number} <span style="font-weight: 400; color: #8b949e; font-size: 0.75rem;">(${v.size_bytes} B)</span></div>
            <div style="color: #94a3b8; font-size: 0.75rem;">${v.change_summary || 'Saved'} &bull; ${v.created_at}</div>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" style="font-size: 0.72rem; padding: 0.2rem 0.45rem;" onclick="restoreVersion(${v.id}, ${v.version_number})">
            Restore
          </button>
        </div>
      `;
    });
    versionsListContainer.innerHTML = html;
  }

  window.restoreVersion = async function (versionId, verNum) {
    if (!confirm(`Restore to Version #${verNum}? This creates a new version with the restored content.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/student/files/${activeFileId}/versions/${versionId}/restore`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success) {
        setContent(data.file.content, data.file.filename);
        loadVersionsList(activeFileId);
        alert(data.message);
      } else {
        alert(data.error || 'Failed to restore version.');
      }
    } catch (e) {
      alert('Error restoring version: ' + e.message);
    }
  };

  /**
   * 6. Create New File
   */
  window.createNewFilePrompt = async function () {
    const filename = prompt('Enter new filename (e.g. script.py, index.html, App.java, style.css):', 'new_file.py');
    if (!filename || !filename.trim()) return;

    try {
      const res = await fetch('/api/student/files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: filename.trim(),
          content: `# ${filename.trim()}\n`
        })
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = `/student/editor/${data.file.id}`;
      } else {
        alert(data.error || 'Failed to create file.');
      }
    } catch (e) {
      alert('Error creating file: ' + e.message);
    }
  };

  /**
   * 7. Rename File
   */
  window.renameCurrentFile = async function (fileId, currentName) {
    const newName = prompt('Enter new filename:', currentName || activeFileName);
    if (!newName || !newName.trim() || newName === currentName) return;

    try {
      const res = await fetch(`/api/student/files/${fileId || activeFileId}/rename`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_filename: newName.trim() })
      });
      const data = await res.json();
      if (data.success) {
        activeFileName = data.file.filename;
        activeLanguage = getLanguageFromFilename(activeFileName);
        updateUIHeader();
        window.location.reload();
      } else {
        alert(data.error || 'Failed to rename file.');
      }
    } catch (e) {
      alert('Error renaming file: ' + e.message);
    }
  };

  /**
   * 8. Duplicate File
   */
  window.duplicateCurrentFile = async function (fileId) {
    try {
      const res = await fetch(`/api/student/files/${fileId || activeFileId}/duplicate`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = `/student/editor/${data.file.id}`;
      } else {
        alert(data.error || 'Failed to duplicate file.');
      }
    } catch (e) {
      alert('Error duplicating file: ' + e.message);
    }
  };

  /**
   * 9. Delete File
   */
  window.deleteCurrentFile = async function (fileId, fname) {
    if (!confirm(`Are you sure you want to delete '${fname || activeFileName}'?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/student/files/${fileId || activeFileId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = '/student/editor';
      } else {
        alert(data.error || 'Failed to delete file.');
      }
    } catch (e) {
      alert('Error deleting file: ' + e.message);
    }
  };

  /**
   * 10. Download Current File
   */
  window.downloadCurrentFile = function () {
    if (!activeFileId) return;
    window.location.href = `/api/student/files/${activeFileId}/download`;
  };

  /**
   * 11. Upload File Handler
   */
  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/student/files/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = `/student/editor/${data.file.id}`;
      } else {
        alert(data.error || 'Upload failed.');
      }
    } catch (err) {
      alert('Upload error: ' + err.message);
    }
  }

  /**
   * 12. Setup Event Listeners
   */
  function setupEventListeners() {
    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        handleSave(true, 'Manual save');
      });
    }

    if (downloadBtn) {
      downloadBtn.addEventListener('click', window.downloadCurrentFile);
    }

    if (newFileBtn) {
      newFileBtn.addEventListener('click', window.createNewFilePrompt);
    }

    if (uploadFileInput) {
      uploadFileInput.addEventListener('change', handleFileUpload);
    }

    if (themeSelect) {
      themeSelect.addEventListener('change', function (e) {
        currentTheme = e.target.value;
        if (editor && window.monaco) {
          monaco.editor.setTheme(currentTheme);
        }
      });
    }

    if (fontIncBtn) {
      fontIncBtn.addEventListener('click', function () {
        if (currentFontSize < 24) {
          currentFontSize += 1;
          if (editor) editor.updateOptions({ fontSize: currentFontSize });
        }
      });
    }

    if (fontDecBtn) {
      fontDecBtn.addEventListener('click', function () {
        if (currentFontSize > 10) {
          currentFontSize -= 1;
          if (editor) editor.updateOptions({ fontSize: currentFontSize });
        }
      });
    }

    // File search filter
    if (fileSearchInput) {
      fileSearchInput.addEventListener('input', function (e) {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll('.file-tree-item').forEach(function (item) {
          const fname = item.dataset.filename ? item.dataset.filename.toLowerCase() : '';
          item.style.display = fname.includes(q) ? 'flex' : 'none';
        });
      });
    }

    // Warn before unload if unsaved changes exist
    window.addEventListener('beforeunload', function (e) {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    });

    // Toolbar Undo / Redo / Find actions
    const btnUndo = document.getElementById('btnToolbarUndo');
    const btnRedo = document.getElementById('btnToolbarRedo');
    const btnFind = document.getElementById('btnToolbarFind');

    if (btnUndo && editor) {
      btnUndo.addEventListener('click', () => editor.trigger('keyboard', 'undo', null));
    }
    if (btnRedo && editor) {
      btnRedo.addEventListener('click', () => editor.trigger('keyboard', 'redo', null));
    }
    if (btnFind && editor) {
      btnFind.addEventListener('click', () => editor.getAction('actions.find').run());
    }
  }

  // Monaco Loader Integration
  if (window.require) {
    window.require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
    window.require(['vs/editor/editor.main'], function () {
      initEditor();
    });
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      initEditor();
    });
  }
})();
