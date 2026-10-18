'use client';

import React, { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from '@tanstack/react-table';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown } from 'lucide-react';

interface DataTableProps {
  data: Record<string, any>[];
  columns?: string[];
  pageSize?: number;
}

export function DataTable({ data, columns: propColumns, pageSize = 15 }: DataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  // Dynamically compute columns if not passed
  const cols = useMemo<ColumnDef<Record<string, any>>[]>(() => {
    if (!data || data.length === 0) return [];
    const keys = propColumns || Object.keys(data[0] || {});
    return keys.map((key) => ({
      accessorKey: key,
      header: ({ column }) => (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="flex items-center gap-1 font-semibold text-foreground text-xs hover:text-primary transition-colors text-left"
        >
          <span>{key.replace(/_/g, ' ')}</span>
          <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
        </button>
      ),
      cell: (info) => {
        const val = info.getValue();
        if (val === null || val === undefined) {
          return <span className="text-muted-foreground/40 italic font-mono text-[11px]">null</span>;
        }
        if (typeof val === 'number') {
          return <span className="font-mono text-xs">{val.toLocaleString()}</span>;
        }
        return <span className="text-xs truncate max-w-[200px] block">{String(val)}</span>;
      },
    }));
  }, [data, propColumns]);

  const table = useReactTable({
    data,
    columns: cols,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    initialState: {
      pagination: { pageSize },
    },
  });

  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-xs text-muted-foreground bg-card/40 rounded-xl border border-border">
        No records available to display.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="border border-border rounded-xl overflow-hidden bg-card shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-secondary/40 border-b border-border">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="py-3 px-4 uppercase tracking-wider text-[11px] font-semibold text-muted-foreground">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-border/60">
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-secondary/30 transition-colors">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="py-2.5 px-4 text-foreground font-normal">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between px-2 text-xs text-muted-foreground">
        <div>
          Showing page <span className="font-medium text-foreground">{table.getState().pagination.pageIndex + 1}</span> of{' '}
          <span className="font-medium text-foreground">{table.getPageCount() || 1}</span> ({data.length.toLocaleString()} total rows)
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
            className="p-1.5 rounded-lg border border-border bg-card hover:bg-secondary disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronsLeft className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="p-1.5 rounded-lg border border-border bg-card hover:bg-secondary disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="p-1.5 rounded-lg border border-border bg-card hover:bg-secondary disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
            className="p-1.5 rounded-lg border border-border bg-card hover:bg-secondary disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronsRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
