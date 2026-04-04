'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, ticketApi, Ticket, TicketCategory, TicketPriority, TicketStatus, User } from '@/lib/api';
import TicketQuickActions from '@/components/TicketQuickActions';

export default function TicketsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('');
  const [categoryFilter, setCategoryFilter] = useState<TicketCategory | ''>('');
  const [showMyTicketsOnly, setShowMyTicketsOnly] = useState(false);

  const pageSize = 20;
  const isITStaff = user?.role === 'it_staff' || user?.role === 'admin';

  useEffect(() => {
    void loadUser();
  }, []);

  useEffect(() => {
    if (user) {
      void loadTickets();
    }
  }, [user, page, statusFilter, categoryFilter, showMyTicketsOnly]);

  const loadUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/auth/login');
        return;
      }
      setUser(await authApi.getMe(token));
    } catch (err) {
      console.error('Failed to load user:', err);
      router.push('/auth/login');
    }
  };

  const loadTickets = async () => {
    try {
      setLoading(true);
      setError('');

      const params: {
        page: number;
        page_size: number;
        status?: TicketStatus;
        category?: TicketCategory;
        assignee_id?: string;
      } = { page, page_size: pageSize };

      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (isITStaff && showMyTicketsOnly && user) params.assignee_id = user.id;

      const response = await ticketApi.listTickets(params);
      setTickets(response.tickets);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || '티켓 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const statusClasses: Record<TicketStatus, string> = {
    open: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    resolved: 'bg-green-100 text-green-800',
    on_hold: 'bg-gray-100 text-gray-800',
    closed: 'bg-gray-100 text-gray-600',
  };

  const priorityClasses: Record<TicketPriority, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">티켓</h1>
          <p className="mt-2 text-gray-600">지원 요청을 확인하고 관리합니다.</p>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">상태</label>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as TicketStatus | '');
                  setPage(1);
                }}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                <option value="">전체</option>
                <option value="open">열림</option>
                <option value="in_progress">진행 중</option>
                <option value="resolved">해결됨</option>
                <option value="on_hold">대기 중</option>
                <option value="closed">닫힘</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">카테고리</label>
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value as TicketCategory | '');
                  setPage(1);
                }}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                <option value="">전체</option>
                <option value="account">계정</option>
                <option value="device">장비</option>
                <option value="network">네트워크</option>
                <option value="system">시스템</option>
                <option value="security">보안</option>
                <option value="other">기타</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setStatusFilter('');
                  setCategoryFilter('');
                  setShowMyTicketsOnly(false);
                  setPage(1);
                }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
              >
                필터 초기화
              </button>
            </div>
          </div>

          {isITStaff && (
            <div className="mt-4 border-t border-gray-200 pt-4">
              <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={showMyTicketsOnly}
                  onChange={(e) => {
                    setShowMyTicketsOnly(e.target.checked);
                    setPage(1);
                  }}
                  className="rounded border-gray-300"
                />
                내게 할당된 티켓만 보기
              </label>
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}

        <div className="overflow-hidden rounded-lg bg-white shadow-sm">
          {loading ? (
            <div className="p-12 text-center text-gray-500">티켓 로딩 중...</div>
          ) : tickets.length === 0 ? (
            <div className="p-12 text-center text-gray-500">티켓이 없습니다.</div>
          ) : (
            <>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">번호</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">제목</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">카테고리</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">상태</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">우선순위</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">담당자</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">생성일</th>
                    {isITStaff && (
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">빠른 작업</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {tickets.map((ticket) => (
                    <tr
                      key={ticket.id}
                      onClick={() => router.push(`/tickets/${ticket.id}`)}
                      className="cursor-pointer hover:bg-gray-50"
                    >
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                        #{ticket.ticket_number}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="max-w-md truncate">{ticket.title}</div>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{ticket.category}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusClasses[ticket.status]}`}>
                          {ticket.status}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${priorityClasses[ticket.priority]}`}>
                          {ticket.priority}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {ticket.assignee_name || '-'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {formatDate(ticket.created_at)}
                      </td>
                      {isITStaff && user && (
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <TicketQuickActions ticket={ticket} user={user} onUpdate={() => void loadTickets()} />
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>

              {totalPages > 1 && (
                <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-6 py-4">
                  <div className="text-sm text-gray-700">
                    총 <span className="font-medium">{total}</span>개 티켓, {page}/{totalPages} 페이지
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                      className="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
                    >
                      이전
                    </button>
                    <button
                      onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                      className="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
                    >
                      다음
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
