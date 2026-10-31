import { Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2, Clock3, CloudUpload, Code2, Copy, Database, FileImage, FileSearch, Fingerprint, Image as ImageIcon, LoaderCircle, RefreshCw, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';

export default function PublicEndpointScreen(props) {
  const { activeTab, PageHeading, ImageWorkspace, SignInCard, EmptyState, EndpointCard, selectedFile, previewUrl, chooseFile, busy, checkMetadata, checkResult, removeSelectedFile, loadSampleImage, showToast, cleanMetadata, lastClean, verifyCleanedFile, token, endpoints, newEndpointName, setNewEndpointName, createEndpoint, editingId, editingName, setEditingId, setEditingName, saveEndpointName, deleteEndpoint, endpointFiles, setEndpointFiles, endpointModes, setEndpointModes, uploadEndpointImage, uploadingEndpoint, copyText, activities, refreshAccountData, publicId, setPublicId, loadPublicEndpoint, publicLoading, publicData, apiUrl, deleteEndpointImage, formatDate } = props;
  return (
    <>
          {activeTab === 'public' && (
            <>
              <PageHeading
                eyebrow="PUBLIC API EXPLORER"
                title="Browse a public collection."
                description="Load a read-only endpoint using its endpoint ID. No Google sign-in is required to view or retrieve public images."
                icon={CloudUpload}
              />
              <section className="panel">
                <form className="public-search" onSubmit={(e) => { e.preventDefault(); loadPublicEndpoint(); }}>
                  <div className="input-with-icon">
                    <Code2 size={17} />
                    <input
                      value={publicId}
                      onChange={(e) => setPublicId(e.target.value)}
                      placeholder="Paste endpoint ID here (e.g. from My Endpoints)"
                      aria-label="Public endpoint ID"
                    />
                  </div>
                  <button className="primary-button" disabled={publicLoading}>
                    {publicLoading ? <LoaderCircle className="spin" size={16} /> : <ArrowRight size={16} />} Load endpoint
                  </button>
                </form>
                {publicData && (
                  <div className="public-results">
                    <div className="public-title">
                      <div>
                        <span className="eyebrow">PUBLIC COLLECTION</span>
                        <h2>{publicData.endpoint?.name || 'Unnamed endpoint'}</h2>
                        <p>{publicData.images?.length || 0} stored images</p>
                      </div>
                      <button className="secondary-button" onClick={() => copyText(apiUrl(`/api/public/${publicId}`))}>
                        <Copy size={15} /> Copy API URL
                      </button>
                    </div>
                    {publicData.images?.length ? (
                      <div className="image-grid">
                        {publicData.images.map((image) => (
                          <div className="stored-image" key={image.image_id}>
                            <a href={apiUrl(image.url)} target="_blank" rel="noreferrer">
                              <img src={apiUrl(image.url)} alt={image.filename} loading="lazy" />
                            </a>
                            <div className="stored-image-info">
                              <b title={image.filename}>{image.filename}</b>
                              <small>{image.format} · {image.marker_count} known markers</small>
                              {token && (
                                <button className="text-danger" onClick={() => deleteEndpointImage(publicId, image.image_id)}>
                                  <Trash2 size={14} /> Delete image
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        icon={ImageIcon}
                        title="No images in this endpoint"
                        text="This endpoint exists, but it does not have any stored images yet."
                      />
                    )}
                  </div>
                )}
              </section>
            </>
          )}


    </>
  );
}

