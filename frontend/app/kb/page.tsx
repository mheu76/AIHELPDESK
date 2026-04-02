'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ApiError, KBDocument, KBSearchResult, kbApi } from '@/lib/api';

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md'];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function KBManagementPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<KBDocument | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<KBSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  useEffect(() => {
    void loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await kbApi.listDocuments(100, 0);
      setDocuments(response.documents);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError('Only admins and IT staff can manage the knowledge base.');
      } else {
        setError('Failed to load documents.');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentDetail = async (docId: string) => {
    try {
      setDetailLoading(true);
      const document = await kbApi.getDocument(docId);
      setSelectedDocument(document);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load document details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const validateFile = (file: File): string | null => {
    const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0];

    if (!extension || !SUPPORTED_EXTENSIONS.includes(extension)) {
      return `Unsupported file type. Allowed: ${SUPPORTED_EXTENSIONS.join(', ')}`;
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be 10MB or smaller.';
    }

    return null;
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    let progressInterval: ReturnType<typeof setInterval> | undefined;

    try {
      setUploading(true);
      setError(null);
      setUploadProgress(0);

      progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev === null || prev >= 90) return prev;
          return prev + 10;
        });
      }, 200);

      const uploaded = await kbApi.uploadDocument(file);
      await loadDocuments();
      await loadDocumentDetail(uploaded.id);
      setUploadProgress(100);

      window.setTimeout(() => {
        setUploadProgress(null);
      }, 1000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed.');
    } finally {
      if (progressInterval) clearInterval(progressInterval);
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!window.confirm('Delete this document?')) return;

    try {
      await kbApi.deleteDocument(docId);
      if (selectedDocument?.id === docId) {
        setSelectedDocument(null);
      }
      await loadDocuments();
      setSearchResults((prev) =>
        prev.filter((result) => result.metadata.document_id !== docId && result.metadata.id !== docId)
      );
    } catch {
      setError('Delete failed.');
    }
  };

  const handleSearch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      setError(null);
      const response = await kbApi.search(searchQuery.trim(), 5);
      setSearchResults(response.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Search failed.');
    } finally {
      setSearching(false);
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    }

    if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files.length > 0) {
      void handleFileUpload(e.dataTransfer.files);
    }
  };

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  const formatFileSize = (bytes?: number | null) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <button
              onClick={() => router.push('/chat')}
              className="mb-4 text-sm text-gray-600 hover:text-gray-900"
            >
              Back to chat
            </button>
            <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
            <p className="mt-2 text-sm text-gray-600">
              Upload internal guides and search the document corpus used by the assistant.
            </p>
          </div>
          <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
            <div className="font-semibold">Documents</div>
            <div className="mt-1 text-2xl font-bold">{documents.length}</div>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="space-y-6">
            <div
              className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
              } ${uploading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => !uploading && document.getElementById('fileInput')?.click()}
            >
              <input
                id="fileInput"
                type="file"
                className="hidden"
                accept={SUPPORTED_EXTENSIONS.join(',')}
                disabled={uploading}
                onChange={(e) => void handleFileUpload(e.target.files)}
              />

              <p className="text-sm text-gray-600">
                {uploading ? 'Uploading document...' : 'Drop a file here or click to upload.'}
              </p>
              <p className="mt-2 text-xs text-gray-500">PDF, DOCX, TXT, MD up to 10MB.</p>

              {uploadProgress !== null && (
                <div className="mx-auto mt-4 max-w-xs">
                  <div className="h-2 w-full rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">{uploadProgress}% complete</p>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 px-5 py-4">
                <h2 className="text-lg font-semibold text-gray-900">Documents</h2>
                <p className="mt-1 text-sm text-gray-500">Select a document to inspect its details.</p>
              </div>

              {loading ? (
                <div className="py-12 text-center text-sm text-gray-500">Loading documents...</div>
              ) : documents.length === 0 ? (
                <div className="py-12 text-center text-sm text-gray-500">No documents uploaded yet.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Document</th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Chunks</th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Created</th>
                        <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {documents.map((doc) => (
                        <tr
                          key={doc.id}
                          className={`cursor-pointer hover:bg-gray-50 ${
                            selectedDocument?.id === doc.id ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => void loadDocumentDetail(doc.id)}
                        >
                          <td className="px-6 py-4">
                            <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                            <div className="text-xs text-gray-500">{doc.file_name}</div>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{doc.file_type.toUpperCase()}</td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{doc.chunk_count}</td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{formatDate(doc.created_at)}</td>
                          <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleDelete(doc.id);
                              }}
                              className="text-red-600 hover:text-red-900"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>

          <section className="space-y-6">
            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 px-5 py-4">
                <h2 className="text-lg font-semibold text-gray-900">Search</h2>
                <p className="mt-1 text-sm text-gray-500">Search the knowledge base and inspect matching documents.</p>
              </div>

              <form onSubmit={handleSearch} className="space-y-4 px-5 py-4">
                <div className="flex gap-3">
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Example: password reset policy"
                    className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                  <button
                    type="submit"
                    disabled={searching || !searchQuery.trim()}
                    className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {searching ? 'Searching...' : 'Search'}
                  </button>
                </div>
              </form>

              <div className="border-t border-gray-100 px-5 py-4">
                {searchResults.length === 0 ? (
                  <p className="text-sm text-gray-500">No search results yet.</p>
                ) : (
                  <div className="space-y-3">
                    {searchResults.map((result, index) => (
                      <button
                        key={`${result.metadata.document_id ?? result.metadata.id}-${index}`}
                        onClick={() => void loadDocumentDetail(result.metadata.document_id ?? result.metadata.id)}
                        className="block w-full rounded-lg border border-gray-200 p-4 text-left hover:border-blue-300 hover:bg-blue-50"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div className="text-sm font-semibold text-gray-900">
                            {result.metadata.title ?? 'Untitled'}
                          </div>
                          <div className="text-xs text-gray-500">
                            Score {typeof result.relevance_score === 'number' ? result.relevance_score.toFixed(2) : '-'}
                          </div>
                        </div>
                        <div className="mt-1 text-xs uppercase tracking-wide text-gray-500">
                          {result.metadata.file_type?.toUpperCase() ?? 'DOC'}
                        </div>
                        <p className="mt-3 line-clamp-4 text-sm leading-6 text-gray-700">{result.content}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 px-5 py-4">
                <h2 className="text-lg font-semibold text-gray-900">Document details</h2>
                <p className="mt-1 text-sm text-gray-500">Metadata and extracted content for the selected document.</p>
              </div>

              {detailLoading ? (
                <div className="px-5 py-12 text-center text-sm text-gray-500">Loading document details...</div>
              ) : selectedDocument ? (
                <div className="space-y-5 px-5 py-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <InfoCard label="Title" value={selectedDocument.title} />
                    <InfoCard label="File name" value={selectedDocument.file_name} />
                    <InfoCard
                      label="Type / Size"
                      value={`${selectedDocument.file_type.toUpperCase()} / ${formatFileSize(selectedDocument.file_size)}`}
                    />
                    <InfoCard
                      label="Chunks / Created"
                      value={`${selectedDocument.chunk_count} / ${formatDate(selectedDocument.created_at)}`}
                    />
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-semibold text-gray-900">Content</div>
                    <div className="max-h-[420px] overflow-y-auto rounded-lg bg-slate-950 p-4 text-sm leading-6 text-slate-100">
                      <pre className="whitespace-pre-wrap break-words font-sans">
                        {selectedDocument.content?.trim() || 'No extracted content.'}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="px-5 py-12 text-center text-sm text-gray-500">
                  Select a document from the list or search results.
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="mt-1 text-sm font-medium text-gray-900">{value}</div>
    </div>
  );
}
