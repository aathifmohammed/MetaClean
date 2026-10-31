import { Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2, Clock3, CloudUpload, Code2, Copy, Database, FileImage, FileSearch, Fingerprint, Image as ImageIcon, LoaderCircle, RefreshCw, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';

export default function CheckMetadataScreen(props) {
  const { activeTab, PageHeading, ImageWorkspace, SignInCard, EmptyState, EndpointCard, selectedFile, previewUrl, chooseFile, busy, checkMetadata, checkResult, removeSelectedFile, loadSampleImage, showToast, cleanMetadata, lastClean, verifyCleanedFile, token, endpoints, newEndpointName, setNewEndpointName, createEndpoint, editingId, editingName, setEditingId, setEditingName, saveEndpointName, deleteEndpoint, endpointFiles, setEndpointFiles, endpointModes, setEndpointModes, uploadEndpointImage, uploadingEndpoint, copyText, activities, refreshAccountData, publicId, setPublicId, loadPublicEndpoint, publicLoading, publicData, apiUrl, deleteEndpointImage, formatDate } = props;
  return (
    <>
          {activeTab === 'check' && (
            <>
              <PageHeading
                eyebrow="AI IMAGE INSPECTOR"
                title="Detect AI markers & inspect metadata."
                description="Scan images for known AI generator signatures (Midjourney, DALL-E, Stable Diffusion, Firefly), C2PA credentials, and EXIF/XMP tags."
                icon={FileSearch}
              />
              <ImageWorkspace
                selectedFile={selectedFile}
                previewUrl={previewUrl}
                chooseFile={chooseFile}
                busy={busy}
                checkMetadata={checkMetadata}
                checkResult={checkResult}
                setSelectedFile={removeSelectedFile}
                loadSampleImage={loadSampleImage}
                showToast={showToast}
              />
            </>
          )}


    </>
  );
}

