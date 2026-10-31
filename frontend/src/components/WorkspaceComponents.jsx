import { useMemo, useState } from 'react';
import { Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2, CircleHelp, Clock3, CloudUpload, Code2, Copy, Database, FileImage, FileSearch, Fingerprint, Image as ImageIcon, LoaderCircle, LogIn, Menu, Search, ShieldCheck, Sparkles, Trash2, Upload, UserRound, X, Zap } from 'lucide-react';
import { formatDate } from '../api';
export function PageHeading({ title, description }) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
    </div>
  );
}

export function SignInCard() {
  return (
    <section className="signin-card">
      <div className="signin-icon"><LogIn size={24} /></div>
      <h2>Sign in to unlock endpoints & activity history</h2>
      <p>Google sign-in is required for creating named endpoints, storage, and action logs. Guest checking and cleaning are 100% available without signing in.</p>
      <div className="signin-inline">
        <span>Verified by Google OAuth</span>
      </div>
    </section>
  );
}

export function ImageWorkspace({
  selectedFile,
  previewUrl,
  chooseFile,
  busy,
  checkMetadata,
  checkResult,
  setSelectedFile,
  cleanMetadata,
  cleaningMode = '',
  cleanView = false,
  lastClean,
  loadSampleImage,
  verifyCleanedFile,
  showToast,
}) {
  const [dragging, setDragging] = useState(false);
  const inputId = cleanView ? 'clean-image-input' : 'check-image-input';
  const onDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files?.[0]);
  };

  const hasAiMarkers = checkResult ? checkResult.ai_marker_count > 0 : false;


  return (
    <div className="workspace-grid">
      <div className="workspace-main">
        <section className="panel upload-panel">
          <div className="panel-heading">
            <div>
              <h2>{cleanView ? 'Choose an image to clean' : 'Choose an image to inspect for AI markers'}</h2>
              <p>Supported formats: JPEG, PNG, WEBP · Max file size: 10 MB</p>
            </div>
          </div>

          {!selectedFile ? (
            <>
              <label
                htmlFor={inputId}
                className={`dropzone ${dragging ? 'dragging' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
              >
                <input
                  id={inputId}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                  onChange={(e) => chooseFile(e.target.files?.[0])}
                  hidden
                />
                <div className="upload-icon"><CloudUpload size={27} /></div>
                <strong>Drop your image here</strong>
                <span>or <u>browse files</u> from your device</span>
                <small>JPG · PNG · WEBP</small>
              </label>

            </>
          ) : (
            <div className="selected-file">
              <div className="selected-preview">
                {previewUrl ? <img src={previewUrl} alt="Selected preview" /> : <ImageIcon />}
              </div>
              <div className="selected-details">
                <b>{selectedFile.name}</b>
                <span>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB · {selectedFile.type || 'Image file'}</span>
                <label className="replace-link" htmlFor={`${inputId}-replace`}>
                  Choose a different image
                  <input
                    id={`${inputId}-replace`}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                    hidden
                    onChange={(e) => chooseFile(e.target.files?.[0])}
                  />
                </label>
              </div>
              <button className="icon-button" title="Remove selected image" onClick={() => setSelectedFile(null)}>
                <X size={17} />
              </button>
            </div>
          )}

          {cleanView && checkResult && (
            <div className="clean-status-bar">
              {hasAiMarkers ? (
                <span className="clean-status-ai">
                  {checkResult.ai_marker_count} AI marker{checkResult.ai_marker_count > 1 ? 's' : ''} detected — choose how to clean:
                </span>
              ) : (
                <span className="clean-status-clean">
                  No AI metadata found — you can remove all metadata for complete privacy.
                </span>
              )}
            </div>
          )}
          {cleanView && !checkResult && selectedFile && (
            <div className="clean-status-bar">
              <span className="clean-status-pending">
                <LoaderCircle className="spin" size={14} />
                Scanning image for AI markers…
              </span>
            </div>
          )}

          <div className="action-row">
            {cleanView ? (
              <div className="clean-action-buttons">
                {hasAiMarkers && (
                  <button
                    className="btn-clean-ai large"
                    id="clean-ai-only-btn"
                    disabled={!selectedFile || busy || Boolean(cleaningMode)}
                    onClick={() => cleanMetadata('ai_only')}
                  >
                    {cleaningMode === 'ai_only' && <LoaderCircle className="spin" size={17} />}
                    {cleaningMode === 'ai_only' ? 'Cleaning…' : 'Remove AI Metadata Only'}
                  </button>
                )}
                <button
                  className="btn-clean-all large"
                  id="clean-all-btn"
                  disabled={!selectedFile || busy || Boolean(cleaningMode)}
                  onClick={() => cleanMetadata('all')}
                >
                  {cleaningMode === 'all' && <LoaderCircle className="spin" size={17} />}
                  {cleaningMode === 'all' ? 'Cleaning…' : 'Remove All Metadata'}
                </button>
              </div>
            ) : (
              <button
                className="primary-button large"
                disabled={!selectedFile || busy}
                onClick={() => checkMetadata()}
              >
                {busy ? <LoaderCircle className="spin" size={17} /> : <FileSearch size={17} />}
                {busy ? 'Scanning image…' : 'Check Image Metadata'}
              </button>
            )}
          </div>
        </section>

        {cleanView && lastClean && (
          <section className="success-card">
            <div>
              <b>{lastClean.filename}</b>
              <span>
                Downloaded · {(lastClean.size / 1024).toFixed(1)} KB ·{' '}
                {lastClean.mode === 'all' ? 'All metadata stripped' : 'AI metadata removed, photo EXIF retained'}
              </span>
              {verifyCleanedFile && (
                <div>
                  <button className="verify-badge-action" onClick={verifyCleanedFile}>
                    Verify Cleaned Image (Inspect in Detector)
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {!cleanView && checkResult && (
          <MetadataResults
            result={checkResult}
            showToast={showToast}
          />
        )}

        {cleanView && (
          <section className="info-banner">
            <div>
              <b>How does cleaning work?</b>
              <p>
                <b>AI metadata only</b> removes known AI generator signatures, prompt descriptions, and model workflows (such as Midjourney, Stable Diffusion, DALL-E) while retaining camera settings (ISO, shutter, camera model, artist).<br />
                <b>All metadata</b> completely re-encodes the image without copying any EXIF, XMP, IPTC, ICC, or C2PA manifest blocks for maximum privacy.
              </p>
            </div>
          </section>
        )}
      </div>

      <aside className="workspace-aside">
        <div className="aside-card">
          <div className="aside-icon"><Zap size={19} /></div>
          <h3>{cleanView ? 'Privacy protection' : 'Detection intelligence'}</h3>
          <p>
            {cleanView
              ? 'Easily remove embedded AI tags, prompts, or sensitive location/camera data before sharing on social media or platforms.'
              : 'Inspect embedded EXIF, XMP, IPTC, and C2PA Content Credentials for AI generator markers.'}
          </p>
          <ul>
            <li><CheckCircle2 size={15} /> Midjourney, DALL-E, SDXL, Firefly</li>
            <li><CheckCircle2 size={15} /> C2PA digital source type check</li>
            <li><CheckCircle2 size={15} /> Selective or complete cleaning</li>
            <li><CheckCircle2 size={15} /> One-click download & verify</li>
          </ul>
        </div>
        <div className="aside-card muted-card">
          <div className="aside-icon"><Fingerprint size={19} /></div>
          <h3>About AI markers</h3>
          <p>
            AI image generators typically write signature metadata into EXIF/XMP tags (e.g. software name, generation parameters, or C2PA trainedAlgorithmicMedia declarations). MetaClean finds and strips these markers accurately.
          </p>
        </div>
      </aside>
    </div>
  );
}

export function MetadataResults({ result, showToast }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('ALL');

  const metadataList = useMemo(() => {
    return Array.isArray(result.metadata) ? result.metadata : [];
  }, [result.metadata]);

  const markers = useMemo(() => {
    return Array.isArray(result.ai_markers) ? result.ai_markers : [];
  }, [result.ai_markers]);

  const c2pa = result.c2pa || {};

  // Categorize metadata
  const filteredList = useMemo(() => {
    return metadataList.filter((item) => {
      const key = String(item.key || '').toLowerCase();
      const val = String(item.value || '').toLowerCase();
      const matchesSearch = !searchTerm || key.includes(searchTerm.toLowerCase()) || val.includes(searchTerm.toLowerCase());
      if (!matchesSearch) return false;

      if (category === 'EXIF') return key.startsWith('exif:') || key.startsWith('ifd') || key.startsWith('maker');
      if (category === 'XMP') return key.startsWith('xmp:') || key.startsWith('xmp-');
      if (category === 'IPTC') return key.startsWith('iptc:');
      if (category === 'PNG') return key.startsWith('png:');
      return true;
    });
  }, [metadataList, searchTerm, category]);

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      showToast('Metadata copied to clipboard as JSON.');
    } catch {
      showToast('Failed to copy to clipboard.');
    }
  };

  return (
    <section className="panel results-panel">
      <div className="panel-heading">
        <div>
          <h2>{result.filename || 'Image Inspection'}</h2>
          <p>
            {result.format || 'Unknown format'}
            {result.width && result.height ? ` · ${result.width} × ${result.height} px` : ''} ·{' '}
            {(Number(result.file_size_bytes || 0) / 1024).toFixed(1)} KB
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <Metric
          label="Detected AI Markers"
          value={result.ai_marker_count ?? markers.length}
          icon={Fingerprint}
        />
        <Metric
          label="Total Metadata Fields"
          value={result.metadata_count ?? metadataList.length}
          icon={Database}
        />
        <Metric
          label="Image Dimensions"
          value={result.width && result.height ? `${result.width} × ${result.height} px` : 'Unknown'}
          icon={ImageIcon}
        />
      </div>

      {/* AI Markers Section */}
      {markers.length > 0 ? (
        <div className="marker-list">
          <h3>Detected AI Generator Signatures ({markers.length})</h3>
          {markers.map((marker, i) => (
            <div className="marker-item" key={`${marker.name}-${marker.source}-${i}`}>
              <div>
                <b>{marker.name}</b>
                <small>{marker.source} · {marker.description}</small>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-inline" style={{ marginBottom: 16 }}>
          <CheckCircle2 size={18} style={{ color: '#10b981' }} />
          <span><b>Clean:</b> No known AI generator signatures detected in readable metadata fields.</span>
        </div>
      )}

      {/* C2PA Provenance Manifest Section */}
      {c2pa.has_manifest && (
        <div className="c2pa-card">
          <div className="c2pa-header">
            <div className="c2pa-header-title">
              <span>C2PA Content Credentials Manifest</span>
            </div>
          </div>
          <div className="c2pa-details-grid">
            {c2pa.digital_source_type && (
              <div className="c2pa-detail">
                <span>Digital Source Type</span>
                <b>{c2pa.digital_source_type}</b>
              </div>
            )}
            {c2pa.active_manifest && (
              <div className="c2pa-detail">
                <span>Active Manifest</span>
                <b>{c2pa.active_manifest}</b>
              </div>
            )}
            {c2pa.recorded_actions?.length > 0 && (
              <div className="c2pa-detail">
                <span>Recorded Actions</span>
                <b>{c2pa.recorded_actions.join(', ')}</b>
              </div>
            )}
            {c2pa.validation_state && (
              <div className="c2pa-detail">
                <span>Validation State</span>
                <b>{c2pa.validation_state}</b>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Metadata Search, Filters, and Table */}
      <div className="metadata-heading">
        <h3>Readable Image Metadata</h3>
        <button type="button" className="btn-json-copy" onClick={copyJson}>
          <Copy size={13} /> Copy Raw JSON
        </button>
      </div>

      <div className="metadata-controls">
        <div className="metadata-search-wrap">
          <Search size={14} />
          <input
            className="metadata-search-input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search tags or values (e.g. software, artist, prompt, lens)..."
            aria-label="Search metadata"
          />
        </div>
        <div className="category-filter">
          {['ALL', 'EXIF', 'XMP', 'IPTC', 'PNG'].map((cat) => (
            <button
              key={cat}
              type="button"
              className={`cat-pill ${category === cat ? 'active' : ''}`}
              onClick={() => setCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {filteredList.length > 0 ? (
        <div className="metadata-list">
          {filteredList.map((item, index) => (
            <div className="metadata-row" key={`${item.key}-${index}`}>
              <b>{item.key}</b>
              <span>{item.value}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-inline">
          <span>
            {metadataList.length > 0
              ? 'No metadata fields match your search filter.'
              : 'No readable metadata tags found in this file.'}
          </span>
        </div>
      )}

    </section>
  );
}

export function Metric({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, text }) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><Icon size={22} /></div>
      <b>{title}</b>
      <p>{text}</p>
    </div>
  );
}

export function EndpointCard({
  endpoint,
  apiUrl,
  editingId,
  editingName,
  setEditingId,
  setEditingName,
  saveEndpointName,
  deleteEndpoint,
  endpointFiles,
  setEndpointFiles,
  endpointModes,
  setEndpointModes,
  uploadEndpointImage,
  uploadingEndpoint,
  copyText,
}) {
  const publicUrl = apiUrl(`/api/public/${endpoint.endpoint_id}`);
  const fileInputId = `endpoint-file-${endpoint.endpoint_id}`;

  return (
    <article className="endpoint-card">
      <div className="endpoint-card-top">
        <div className="endpoint-symbol"><Code2 size={19} /></div>
        <div className="endpoint-main-info">
          {editingId === endpoint.endpoint_id ? (
            <form className="rename-form" onSubmit={(e) => { e.preventDefault(); saveEndpointName(endpoint.endpoint_id); }}>
              <input
                value={editingName}
                maxLength={80}
                onChange={(e) => setEditingName(e.target.value)}
                autoFocus
              />
              <button className="icon-button" aria-label="Save name"><Check size={16} /></button>
              <button type="button" className="icon-button" onClick={() => setEditingId('')} aria-label="Cancel rename"><X size={16} /></button>
            </form>
          ) : (
            <>
              <h3>{endpoint.name}</h3>
              <p>Created {formatDate(endpoint.created_at)}</p>
            </>
          )}
        </div>
        <span className="small-count">{endpoint.image_count ?? 0}/10 images</span>
      </div>
      <div className="endpoint-url">
        <span>{publicUrl}</span>
        <button className="icon-button" title="Copy public API URL" onClick={() => copyText(publicUrl)}>
          <Copy size={15} />
        </button>
      </div>
      <div className="endpoint-actions">
        <button className="secondary-button" onClick={() => { setEditingId(endpoint.endpoint_id); setEditingName(endpoint.name); }}>
          <UserRound size={14} /> Rename
        </button>
        <button className="secondary-button danger-outline" onClick={() => deleteEndpoint(endpoint)}>
          <Trash2 size={14} /> Delete endpoint
        </button>
      </div>
      <div className="endpoint-upload">
        <div className="endpoint-upload-title">
          <CloudUpload size={16} />
          <b>Save a cleaned image to this endpoint</b>
        </div>
        <div className="endpoint-upload-controls">
          <label className="file-picker" htmlFor={fileInputId}>
            <Upload size={15} />
            <span>{endpointFiles[endpoint.endpoint_id]?.name || 'Choose image to clean & store'}</span>
            <input
              id={fileInputId}
              type="file"
              accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
              hidden
              onChange={(e) => setEndpointFiles((old) => ({ ...old, [endpoint.endpoint_id]: e.target.files?.[0] || null }))}
            />
          </label>
          <select
            aria-label="Image cleaning mode"
            value={endpointModes[endpoint.endpoint_id] || 'all'}
            onChange={(e) => setEndpointModes((old) => ({ ...old, [endpoint.endpoint_id]: e.target.value }))}
          >
            <option value="all">Clean all supported metadata</option>
            <option value="ai_only">Clean AI-related EXIF</option>
          </select>
          <button
            className="primary-button"
            disabled={uploadingEndpoint === endpoint.endpoint_id || !endpointFiles[endpoint.endpoint_id]}
            onClick={() => uploadEndpointImage(endpoint)}
          >
            {uploadingEndpoint === endpoint.endpoint_id ? <LoaderCircle className="spin" size={15} /> : <ArrowDownToLine size={15} />} Save
          </button>
        </div>
        <small>Images are automatically cleaned by the backend before being saved to Cloudflare R2.</small>
      </div>
    </article>
  );
}

