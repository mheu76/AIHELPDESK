'use client'

import { FormEvent, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

import { ApiError, KBDocument, KBSearchResult, kbApi } from '@/lib/api'

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']
const MAX_FILE_SIZE = 10 * 1024 * 1024

export default function KBManagementPage() {
  const router = useRouter()
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [selectedDocument, setSelectedDocument] = useState<KBDocument | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<KBSearchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  useEffect(() => {
    void loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const response = await kbApi.listDocuments(100, 0)
      setDocuments(response.documents)
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError('KB 관리는 관리자 또는 IT 담당자만 사용할 수 있습니다.')
      } else {
        setError('문서 목록을 불러오지 못했습니다.')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadDocumentDetail = async (docId: string) => {
    try {
      setDetailLoading(true)
      const document = await kbApi.getDocument(docId)
      setSelectedDocument(document)
      setError(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '문서 상세 정보를 불러오지 못했습니다.')
    } finally {
      setDetailLoading(false)
    }
  }

  const validateFile = (file: File): string | null => {
    const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0]

    if (!extension || !SUPPORTED_EXTENSIONS.includes(extension)) {
      return `지원 형식이 아닙니다. ${SUPPORTED_EXTENSIONS.join(', ')} 파일만 업로드할 수 있습니다.`
    }

    if (file.size > MAX_FILE_SIZE) {
      return '파일 크기는 10MB를 초과할 수 없습니다.'
    }

    return null
  }

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return

    const file = files[0]
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    let progressInterval: ReturnType<typeof setInterval> | undefined

    try {
      setUploading(true)
      setError(null)
      setUploadProgress(0)

      progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev === null || prev >= 90) return prev
          return prev + 10
        })
      }, 200)

      const uploaded = await kbApi.uploadDocument(file)
      await loadDocuments()
      await loadDocumentDetail(uploaded.id)
      setUploadProgress(100)

      window.setTimeout(() => {
        setUploadProgress(null)
      }, 1000)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '파일 업로드에 실패했습니다.')
    } finally {
      if (progressInterval) clearInterval(progressInterval)
      setUploading(false)
    }
  }

  const handleDelete = async (docId: string) => {
    if (!window.confirm('이 문서를 삭제하시겠습니까?')) return

    try {
      await kbApi.deleteDocument(docId)
      if (selectedDocument?.id === docId) {
        setSelectedDocument(null)
      }
      await loadDocuments()
      setSearchResults((prev) =>
        prev.filter((result) => result.metadata.document_id !== docId && result.metadata.id !== docId)
      )
    } catch {
      setError('문서 삭제에 실패했습니다.')
    }
  }

  const handleSearch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    try {
      setSearching(true)
      setError(null)
      const response = await kbApi.search(searchQuery.trim(), 5)
      setSearchResults(response.results)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'KB 검색에 실패했습니다.')
    } finally {
      setSearching(false)
    }
  }

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    }

    if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files.length > 0) {
      void handleFileUpload(e.dataTransfer.files)
    }
  }

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })

  const formatFileSize = (bytes?: number | null) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <button
              onClick={() => router.push('/chat')}
              className="mb-4 text-sm text-gray-600 hover:text-gray-900"
            >
              채팅으로 돌아가기
            </button>
            <h1 className="text-3xl font-bold text-gray-900">지식베이스 관리</h1>
            <p className="mt-2 text-sm text-gray-600">
              IT 매뉴얼, FAQ, 정책 문서를 업로드하고 검색 결과와 원문을 함께 검수합니다.
            </p>
          </div>
          <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
            <div className="font-semibold">현재 문서 수</div>
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

              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>

              <p className="mt-2 text-sm text-gray-600">
                {uploading ? (
                  '문서를 업로드하는 중입니다.'
                ) : (
                  <>
                    파일을 끌어다 놓거나 클릭해서 업로드하세요.
                    <br />
                    <span className="text-xs text-gray-500">
                      PDF, DOCX, TXT, MD 형식을 지원하며 최대 10MB까지 업로드할 수 있습니다.
                    </span>
                  </>
                )}
              </p>

              {uploadProgress !== null && (
                <div className="mx-auto mt-4 max-w-xs">
                  <div className="h-2 w-full rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">{uploadProgress}% 완료</p>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 px-5 py-4">
                <h2 className="text-lg font-semibold text-gray-900">문서 목록</h2>
                <p className="mt-1 text-sm text-gray-500">
                  문서를 선택하면 오른쪽에서 상세 내용과 메타데이터를 확인할 수 있습니다.
                </p>
              </div>

              {loading ? (
                <div className="py-12 text-center">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-b-2 border-gray-900" />
                  <p className="mt-2 text-sm text-gray-600">문서 목록을 불러오는 중입니다.</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="py-12 text-center text-gray-500">아직 업로드된 문서가 없습니다.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          문서명
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          형식
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          청크 수
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          업로드 일시
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                          작업
                        </th>
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
                          <td className="whitespace-nowrap px-6 py-4">
                            <span className="inline-flex rounded-full bg-blue-100 px-2 text-xs font-semibold leading-5 text-blue-800">
                              {doc.file_type.toUpperCase()}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            {doc.chunk_count}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            {formatDate(doc.created_at)}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                void handleDelete(doc.id)
                              }}
                              className="text-red-600 hover:text-red-900"
                            >
                              삭제
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
                <h2 className="text-lg font-semibold text-gray-900">KB 검색</h2>
                <p className="mt-1 text-sm text-gray-500">
                  실제 질의를 넣어 검색 결과와 근거 문서가 적절한지 바로 점검할 수 있습니다.
                </p>
              </div>

              <form onSubmit={handleSearch} className="space-y-4 px-5 py-4">
                <div className="flex gap-3">
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="예: 비밀번호 재설정 방법"
                    className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                  <button
                    type="submit"
                    disabled={searching || !searchQuery.trim()}
                    className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {searching ? '검색 중...' : '검색'}
                  </button>
                </div>
              </form>

              <div className="border-t border-gray-100 px-5 py-4">
                {searchResults.length === 0 ? (
                  <p className="text-sm text-gray-500">아직 검색 결과가 없습니다.</p>
                ) : (
                  <div className="space-y-3">
                    {searchResults.map((result, index) => (
                      <button
                        key={`${result.metadata.document_id ?? result.metadata.id}-${index}`}
                        onClick={() =>
                          void loadDocumentDetail(result.metadata.document_id ?? result.metadata.id)
                        }
                        className="block w-full rounded-lg border border-gray-200 p-4 text-left transition hover:border-blue-300 hover:bg-blue-50"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div className="text-sm font-semibold text-gray-900">
                            {result.metadata.title ?? '제목 없음'}
                          </div>
                          <div className="text-xs text-gray-500">
                            점수 {typeof result.relevance_score === 'number' ? result.relevance_score.toFixed(2) : '-'}
                          </div>
                        </div>
                        <div className="mt-1 text-xs uppercase tracking-wide text-gray-500">
                          {result.metadata.file_type?.toUpperCase() ?? 'DOC'}
                        </div>
                        <p className="mt-3 line-clamp-4 text-sm leading-6 text-gray-700">
                          {result.content}
                        </p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="border-b border-gray-200 px-5 py-4">
                <h2 className="text-lg font-semibold text-gray-900">문서 상세</h2>
                <p className="mt-1 text-sm text-gray-500">
                  선택한 문서의 본문과 메타데이터를 확인합니다.
                </p>
              </div>

              {detailLoading ? (
                <div className="px-5 py-12 text-center text-sm text-gray-500">문서 상세를 불러오는 중입니다.</div>
              ) : selectedDocument ? (
                <div className="space-y-5 px-5 py-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-lg bg-gray-50 p-3">
                      <div className="text-xs uppercase tracking-wide text-gray-500">제목</div>
                      <div className="mt-1 text-sm font-medium text-gray-900">{selectedDocument.title}</div>
                    </div>
                    <div className="rounded-lg bg-gray-50 p-3">
                      <div className="text-xs uppercase tracking-wide text-gray-500">파일명</div>
                      <div className="mt-1 text-sm font-medium text-gray-900">{selectedDocument.file_name}</div>
                    </div>
                    <div className="rounded-lg bg-gray-50 p-3">
                      <div className="text-xs uppercase tracking-wide text-gray-500">형식 / 크기</div>
                      <div className="mt-1 text-sm font-medium text-gray-900">
                        {selectedDocument.file_type.toUpperCase()} / {formatFileSize(selectedDocument.file_size)}
                      </div>
                    </div>
                    <div className="rounded-lg bg-gray-50 p-3">
                      <div className="text-xs uppercase tracking-wide text-gray-500">청크 수 / 업로드 일시</div>
                      <div className="mt-1 text-sm font-medium text-gray-900">
                        {selectedDocument.chunk_count} / {formatDate(selectedDocument.created_at)}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-semibold text-gray-900">본문</div>
                    <div className="max-h-[420px] overflow-y-auto rounded-lg bg-slate-950 p-4 text-sm leading-6 text-slate-100">
                      <pre className="whitespace-pre-wrap break-words font-sans">
                        {selectedDocument.content?.trim() || '본문이 없습니다.'}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="px-5 py-12 text-center text-sm text-gray-500">
                  문서 목록이나 검색 결과에서 항목을 선택하세요.
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
