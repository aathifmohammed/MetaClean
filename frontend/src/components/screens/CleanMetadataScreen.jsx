import { Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2, Clock3, CloudUpload, Code2, Copy, Database, FileImage, FileSearch, Fingerprint, Image as ImageIcon, LoaderCircle, RefreshCw, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';

export default function CleanMetadataScreen(props) {
  const { activeTab, PageHeading, ImageWorkspace, SignInCard, EmptyState, EndpointCard, selectedFile, previewUrl, chooseFile, busy, checkMetadata, checkResult, removeSelectedFile, loadSampleImage, showToast, cleanMetadata, cleaningMode, lastClean, verifyCleanedFile, token, endpoints, newEndpointName, setNewEndpointName, createEndpoint, editingId, editingName, setEditingId, setEditingName, saveEndpointName, deleteEndpoint, endpointFiles, setEndpointFiles, endpointModes, setEndpointModes, uploadEndpointImage, uploadingEndpoint, copyText, activities, refreshAccountData, publicId, setPublicId, loadPublicEndpoint, publicLoading, publicData, apiUrl, deleteEndpointImage, formatDate } = props;
  return (
    <>
          {activeTab === 'clean' && (
            <>
              <PageHeading
                eyebrow="PRIVACY & CLEANING WORKSPACE"
                title="Clean Metadata"
                description="Remove AI generator markers only (keeping camera EXIF) or scrub all metadata completely. Download your cleaned image instantly."
                icon={Sparkles}
              />
              <ImageWorkspace
                selectedFile={selectedFile}
                previewUrl={previewUrl}
                chooseFile={(file) => chooseFile(file, true)}
                busy={busy}
                checkMetadata={checkMetadata}
                checkResult={checkResult}
                setSelectedFile={removeSelectedFile}
                cleanMetadata={cleanMetadata}
                cleaningMode={cleaningMode}
                cleanView
                lastClean={lastClean}
                loadSampleImage={(type) => loadSampleImage(type, true)}
                verifyCleanedFile={verifyCleanedFile}
                showToast={showToast}
              />
            </>
          )}


    </>
  );
}

