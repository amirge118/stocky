"use client"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface DeleteWatchlistDialogProps {
  open: boolean
  listName: string
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}

export function DeleteWatchlistDialog({
  open,
  listName,
  onOpenChange,
  onConfirm,
}: DeleteWatchlistDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white">Delete list</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-zinc-400">
          Delete <span className="text-white font-medium">{listName}</span>? This
          will remove all stocks in the list and cannot be undone.
        </p>
        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 hover:text-white"
          >
            Cancel
          </Button>
          <Button
            onClick={() => {
              onConfirm()
              onOpenChange(false)
            }}
            className="bg-red-600 hover:bg-red-700 text-white border-0"
          >
            Delete
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
