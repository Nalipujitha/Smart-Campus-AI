/**
 * ByteXL-Inspired Online Coding IDE Engine
 * Manages Monaco Editor instance, multi-language configuration,
 * draft persistence, test case runner, and real-time execution feedback.
 */

(function () {
  'use strict';

  // Global editor state
  let editorInstance = null;
  let currentLanguage = 'python';
  let currentTheme = 'vs-dark';
  let currentFontSize = 14;
  let isDirty = false;
  let isRunning = false;
  let isSubmitting = false;

  // DOM Elements
  const container = document.getElementById('monacoContainer');
  const textareaFallback = document.getElementById('codeFallbackTextarea');
  const runBtn = document.getElementById('btnRunCode');
  const submitBtn = document.getElementById('btnSubmitCode');
  const saveBtn = document.getElementById('btnSaveDraft');
  const resetBtn = document.getElementById('btnResetCode');
  const langSelect = document.getElementById('languageSelector');
  const themeSelect = document.getElementById('themeSelector');
  const fontIncBtn = document.getElementById('btnFontIncrease');
  const fontDecBtn = document.getElementById('btnFontDecrease');
  const statusIndicator = document.getElementById('editorStatusIndicator');
  const executionSpinner = document.getElementById('executionSpinner');
  const consoleOutput = document.getElementById('consoleOutput');
  const consoleError = document.getElementById('consoleError');
  const customInputTextarea = document.getElementById('customInputArea');
  const testResultsContainer = document.getElementById('testResultsContainer');
  const bottomPanel = document.getElementById('bottomConsolePanel');
  const bottomCollapseBtn = document.getElementById('btnToggleConsoleCollapse');

  // Configuration passed from template via data attributes
  const config = {
    problemId: container ? container.dataset.problemId : null,
    problemSlug: container ? container.dataset.problemSlug : null,
    starterCode: container ? container.dataset.starterCode || '' : '',
    initialCode: container ? container.dataset.initialCode || '' : '',
    runUrl: '/api/coding/run',
    submitUrl: '/api/coding/submit',
    draftUrl: '/api/coding/draft/' + (container ? container.dataset.problemId : '')
  };

  /**
   * 1. Initialize Monaco Editor
   */
  function initEditor() {
    if (window.monaco && container) {
      editorInstance = monaco.editor.create(container, {
        value: config.initialCode || config.starterCode || '# Write your Python solution here\n',
        language: 'python',
        theme: currentTheme,
        fontSize: currentFontSize,
        fontFamily: "'Fira Code', 'Consolas', monospace",
        automaticLayout: true,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        roundedSelection: true,
        renderLineHighlight: 'all',
        tabSize: 4,
        insertSpaces: true,
        bracketPairColorization: { enabled: true },
        lineNumbers: 'on',
        cursorBlinking: 'smooth',
        padding: { top: 12, bottom: 12 }
      });

      // Track changes for unsaved indicator
      editorInstance.onDidChangeModelContent(function () {
        setDirty(true);
      });

      // Keyboard shortcuts
      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, function () {
        handleRunCode();
      });

      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, function () {
        handleSubmitCode();
      });

      editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, function () {
        handleSaveDraft();
      });

      if (textareaFallback) textareaFallback.style.display = 'none';
    } else if (textareaFallback) {
      // Fallback if Monaco CDN is unreachable
      textareaFallback.style.display = 'block';
      textareaFallback.value = config.initialCode || config.starterCode || '';
      textareaFallback.addEventListener('input', function () {
        setDirty(true);
      });
    }
  }

  function getCode() {
    if (editorInstance) {
      return editorInstance.getValue();
    }
    if (textareaFallback) {
      return textareaFallback.value;
    }
    return '';
  }

  function setCode(newCode) {
    if (editorInstance) {
      editorInstance.setValue(newCode);
    }
    if (textareaFallback) {
      textareaFallback.value = newCode;
    }
    setDirty(false);
  }

  function setDirty(dirty) {
    isDirty = dirty;
    if (statusIndicator) {
      statusIndicator.innerHTML = dirty
        ? '<span style="color:#eab308;">&bull; Unsaved changes</span>'
        : '<span style="color:#22c55e;">&bull; Saved</span>';
    }
  }

  /**
   * 2. Tab Navigation Helpers
   */
  window.switchConsoleTab = function (tabName) {
    document.querySelectorAll('.console-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.console-pane').forEach(p => p.style.display = 'none');

    const activeBtn = document.querySelector(`.console-tab-btn[data-tab="${tabName}"]`);
    const activePane = document.getElementById(`pane-${tabName}`);

    if (activeBtn) activeBtn.classList.add('active');
    if (activePane) activePane.style.display = 'block';

    if (bottomPanel && bottomPanel.classList.contains('collapsed')) {
      bottomPanel.classList.remove('collapsed');
    }
  };

  window.switchLeftTab = function (tabName) {
    document.querySelectorAll('.ide-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.left-panel-pane').forEach(p => p.style.display = 'none');

    const activeBtn = document.querySelector(`.ide-tab-btn[data-tab="${tabName}"]`);
    const activePane = document.getElementById(`left-pane-${tabName}`);

    if (activeBtn) activeBtn.classList.add('active');
    if (activePane) activePane.style.display = 'block';
  };

  /**
   * 3. Run Custom Code Action
   */
  async function handleRunCode() {
    if (isRunning) return;
    const code = getCode();
    if (!code.trim()) {
      alert('Please enter code before running.');
      return;
    }

    isRunning = true;
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.innerHTML = '<span>⏳ Running...</span>';
    }

    // Switch console to Output pane
    window.switchConsoleTab('output');
    if (consoleOutput) consoleOutput.textContent = 'Executing solution against custom input...';
    if (consoleError) consoleError.textContent = '';

    const customInput = customInputTextarea ? customInputTextarea.value : '';

    try {
      const response = await fetch(config.runUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code,
          language: currentLanguage,
          custom_input: customInput,
          problem_id: config.problemId
        })
      });

      const result = await response.json();

      if (!result.success) {
        if (consoleOutput) consoleOutput.textContent = 'Execution error: ' + (result.error || 'Unknown error');
        return;
      }

      let formattedOutput = '';
      if (result.stdout) {
        formattedOutput += result.stdout;
      } else if (!result.stderr) {
        formattedOutput += '[Program exited with 0 output]';
      }

      if (consoleOutput) {
        consoleOutput.textContent = formattedOutput;
      }

      if (result.stderr) {
        if (consoleError) {
          consoleError.textContent = result.stderr;
          consoleError.style.display = 'block';
        }
      } else if (consoleError) {
        consoleError.style.display = 'none';
      }

      // Show execution status banner in console header
      const execMeta = document.getElementById('executionMetadata');
      if (execMeta) {
        const statusColor = result.status === 'Success' ? '#22c55e' : '#ef4444';
        execMeta.innerHTML = `<span style="color:${statusColor}; font-weight:600;">${result.status}</span> &bull; ⏱️ ${result.execution_time_ms} ms`;
      }
    } catch (err) {
      if (consoleOutput) consoleOutput.textContent = 'Network or server error while running code: ' + err.message;
    } finally {
      isRunning = false;
      if (runBtn) {
        runBtn.disabled = false;
        runBtn.innerHTML = '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/></svg> Run Code';
      }
    }
  }

  /**
   * 4. Submit Code Action (Full Test Suite Evaluation)
   */
  async function handleSubmitCode() {
    if (isSubmitting) return;
    const code = getCode();
    if (!code.trim()) {
      alert('Please enter your solution before submitting.');
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>⏳ Evaluating...</span>';
    }

    // Switch to test results pane
    window.switchConsoleTab('results');
    if (testResultsContainer) {
      testResultsContainer.innerHTML = '<div style="padding:1rem; color:#94a3b8;">Running test cases against test runner sandbox...</div>';
    }

    try {
      const response = await fetch(config.submitUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_id: config.problemId,
          code: code,
          language: currentLanguage
        })
      });

      const data = await response.json();

      if (!data.success) {
        if (testResultsContainer) {
          testResultsContainer.innerHTML = `<div class="alert alert-danger" style="margin:1rem; padding:1rem; background:rgba(239,68,68,0.15); border:1px solid #ef4444; border-radius:6px; color:#fca5a5;">${data.error || 'Submission evaluation failed'}</div>`;
        }
        return;
      }

      renderTestResults(data);
      setDirty(false);
    } catch (err) {
      if (testResultsContainer) {
        testResultsContainer.innerHTML = `<div class="alert alert-danger" style="margin:1rem; color:#ef4444;">Network error: ${err.message}</div>`;
      }
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z"/></svg> Submit Solution';
      }
    }
  }

  /**
   * 5. Render Test Case Evaluation Cards
   */
  function renderTestResults(data) {
    if (!testResultsContainer) return;

    const isAccepted = data.status === 'Accepted';
    const bannerBg = isAccepted ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)';
    const bannerBorder = isAccepted ? '#22c55e' : '#ef4444';
    const bannerColor = isAccepted ? '#4ade80' : '#f87171';

    let html = `
      <div style="padding: 1rem; border-bottom: 1px solid #30363d; background: ${bannerBg}; border-left: 4px solid ${bannerBorder}; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
        <div>
          <span style="font-size: 1.15rem; font-weight: 700; color: ${bannerColor};">${isAccepted ? '🎉 Accepted' : '❌ ' + data.status}</span>
          <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 0.75rem;">Passed ${data.passed_test_cases}/${data.total_test_cases} Test Cases</span>
        </div>
        <div style="font-size: 0.85rem; color: #cbd5e1;">
          <span>Score: <strong>${data.score}/${data.points_max} pts</strong></span>
          <span style="margin-left: 1rem;">⏱️ ${data.execution_time_ms} ms</span>
        </div>
      </div>
      <div style="padding: 1rem;">
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">
    `;

    (data.test_results || []).forEach(function (tr) {
      const chipClass = tr.passed ? 'passed' : 'failed';
      const icon = tr.passed ? '✓' : '✗';
      const label = tr.is_hidden ? `Hidden Case #${tr.case_number}` : `Case #${tr.case_number}`;
      html += `<span class="test-case-chip ${chipClass}">${icon} ${label} (${tr.execution_time_ms}ms)</span>`;
    });

    html += `</div>`;

    if (data.error_message) {
      html += `
        <div style="background: #1c1417; border: 1px solid #da3633; border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.5rem; font-family: monospace; font-size: 0.82rem; color: #f85149; white-space: pre-wrap;">${data.error_message}</div>
      `;
    }

    html += `</div>`;
    testResultsContainer.innerHTML = html;
  }

  /**
   * 6. Save Draft Action
   */
  async function handleSaveDraft() {
    const code = getCode();
    try {
      const response = await fetch(config.draftUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: code,
          language: currentLanguage
        })
      });
      const data = await response.json();
      if (data.success) {
        setDirty(false);
      }
    } catch (e) {
      console.warn('Draft auto-save failed:', e);
    }
  }

  /**
   * 7. Event Listeners Setup
   */
  function setupEventListeners() {
    if (runBtn) runBtn.addEventListener('click', handleRunCode);
    if (submitBtn) submitBtn.addEventListener('click', handleSubmitCode);
    if (saveBtn) saveBtn.addEventListener('click', handleSaveDraft);

    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        if (confirm('Reset editor to the original starter code? Unsaved changes will be lost.')) {
          setCode(config.starterCode);
        }
      });
    }

    if (themeSelect) {
      themeSelect.addEventListener('change', function (e) {
        currentTheme = e.target.value;
        if (editorInstance && window.monaco) {
          monaco.editor.setTheme(currentTheme);
        }
      });
    }

    if (fontIncBtn) {
      fontIncBtn.addEventListener('click', function () {
        if (currentFontSize < 24) {
          currentFontSize += 1;
          if (editorInstance) editorInstance.updateOptions({ fontSize: currentFontSize });
        }
      });
    }

    if (fontDecBtn) {
      fontDecBtn.addEventListener('click', function () {
        if (currentFontSize > 10) {
          currentFontSize -= 1;
          if (editorInstance) editorInstance.updateOptions({ fontSize: currentFontSize });
        }
      });
    }

    if (bottomCollapseBtn && bottomPanel) {
      bottomCollapseBtn.addEventListener('click', function () {
        bottomPanel.classList.toggle('collapsed');
      });
    }

    // Auto-save draft every 60 seconds if changed
    setInterval(function () {
      if (isDirty) {
        handleSaveDraft();
      }
    }, 60000);
  }

  // Load Monaco loader if CDN is available
  if (window.require) {
    window.require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
    window.require(['vs/editor/editor.main'], function () {
      initEditor();
      setupEventListeners();
    });
  } else {
    // Check if monaco global is already injected or init fallback
    document.addEventListener('DOMContentLoaded', function () {
      initEditor();
      setupEventListeners();
    });
  }
})();
