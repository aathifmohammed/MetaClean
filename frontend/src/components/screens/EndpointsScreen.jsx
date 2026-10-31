import { Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2, Clock3, CloudUpload, Code2, Copy, Database, FileImage, FileSearch, Fingerprint, Image as ImageIcon, LoaderCircle, RefreshCw, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';

export default function EndpointsScreen(props) {
  const { activeTab, PageHeading, ImageWorkspace, SignInCard, EmptyState, EndpointCard, selectedFile, previewUrl, chooseFile, busy, checkMetadata, checkResult, removeSelectedFile, loadSampleImage, showToast, cleanMetadata, lastClean, verifyCleanedFile, token, endpoints, newEndpointName, setNewEndpointName, createEndpoint, editingId, editingName, setEditingId, setEditingName, saveEndpointName, deleteEndpoint, endpointFiles, setEndpointFiles, endpointModes, setEndpointModes, uploadEndpointImage, uploadingEndpoint, copyText, activities, refreshAccountData, publicId, setPublicId, loadPublicEndpoint, publicLoading, publicData, apiUrl, deleteEndpointImage, formatDate } = props;
  return (
    <>
          {activeTab === 'endpoints' && (
            <>
              <PageHeading
                eyebrow="SAVED COLLECTIONS"
                title="Manage public API endpoints."
                description="Create public read-only endpoints."
                icon={Code2}
              />
              {!token ? (
                <SignInCard />
              ) : (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Create an endpoint</h2>
                      <p>Each endpoint stores and serves up to 10 of its newest cleaned images via public API.</p>
                    </div>
                    <span className="small-count">{endpoints.length} endpoints</span>
                  </div>
                  <form className="create-form" onSubmit={createEndpoint}>
                    <input
                      value={newEndpointName}
                      onChange={(e) => setNewEndpointName(e.target.value)}
                      maxLength={80}
                      placeholder="e.g. Cleaned Portfolio Photos"
                      aria-label="New endpoint name"
                    />
                    <button className="primary-button" type="submit">
                      <Code2 size={16} /> Create endpoint
                    </button>
                  </form>
                  {endpoints.length === 0 ? (
                    <EmptyState
                      icon={Database}
                      title="No endpoints yet"
                      text="Create your first endpoint to start saving cleaned images."
                    />
                  ) : (
                    <div className="endpoint-list">
                      {endpoints.map((endpoint) => (
                        <EndpointCard
                          key={endpoint.endpoint_id}
                          endpoint={endpoint}
                          token={token}
                          apiUrl={apiUrl}
                          editingId={editingId}
                          editingName={editingName}
                          setEditingId={setEditingId}
                          setEditingName={setEditingName}
                          saveEndpointName={saveEndpointName}
                          deleteEndpoint={deleteEndpoint}
                          endpointFiles={endpointFiles}
                          setEndpointFiles={setEndpointFiles}
                          endpointModes={endpointModes}
                          setEndpointModes={setEndpointModes}
                          uploadEndpointImage={uploadEndpointImage}
                          uploadingEndpoint={uploadingEndpoint}
                          copyText={copyText}
                        />
                      ))}
                    </div>
                  )}
                </section>
              )}
            </>
          )}


    </>
  );
}

