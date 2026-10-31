import { Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2, Clock3, CloudUpload, Code2, Copy, Database, FileImage, FileSearch, Fingerprint, Image as ImageIcon, LoaderCircle, RefreshCw, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';

export default function ActivityScreen(props) {
  const { activeTab, PageHeading, ImageWorkspace, SignInCard, EmptyState, EndpointCard, selectedFile, previewUrl, chooseFile, busy, checkMetadata, checkResult, removeSelectedFile, loadSampleImage, showToast, cleanMetadata, lastClean, verifyCleanedFile, token, endpoints, newEndpointName, setNewEndpointName, createEndpoint, editingId, editingName, setEditingId, setEditingName, saveEndpointName, deleteEndpoint, endpointFiles, setEndpointFiles, endpointModes, setEndpointModes, uploadEndpointImage, uploadingEndpoint, copyText, activities, refreshAccountData, publicId, setPublicId, loadPublicEndpoint, publicLoading, publicData, apiUrl, deleteEndpointImage, formatDate } = props;
  return (
    <>
          {activeTab === 'activity' && (
            <>
              <PageHeading
                eyebrow="RECENT ACTIVITY"
                title="Audit log & operations."
                description="Signed-in activity records are recorded. Displays your latest 10 inspect and clean actions."
                icon={Activity}
              />
              {!token ? (
                <SignInCard />
              ) : (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Activity history</h2>
                      <p>Full images are never saved to history; only operational metadata is tracked.</p>
                    </div>
                    <button className="secondary-button" onClick={() => refreshAccountData(token)}>
                      <RefreshCw size={15} /> Refresh
                    </button>
                  </div>
                  {activities.length === 0 ? (
                    <EmptyState
                      icon={Clock3}
                      title="No activity recorded"
                      text="Check or clean an image while signed in to log your actions here."
                    />
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Operation</th>
                            <th>Filename</th>
                            <th>Known AI markers</th>
                            <th>Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activities.map((row, index) => (
                            <tr key={`${row.filename}-${row.created_at}-${index}`}>
                              <td>
                                <span className="operation-pill">
                                  {{ check_metadata: 'Check Metadata', clean_all: 'Clean All Metadata', clean_ai_only: 'Clean AI Metadata Only' }[row.operation] || String(row.operation).replaceAll('_', ' ')}
                                </span>
                              </td>
                              <td className="filename-cell">
                                <FileImage size={16} />{row.filename}
                              </td>
                              <td>{row.marker_count ?? '—'}</td>
                              <td>{formatDate(row.created_at)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              )}
            </>
          )}


    </>
  );
}

