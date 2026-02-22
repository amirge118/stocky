"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { deleteStock } from "@/lib/api/stocks"
import { useToast } from "@/hooks/use-toast"
import type { Stock } from "@/types/stock"

export interface BulkDeleteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  stocks: Stock[]
  onSuccess?: () => void
}

export function BulkDeleteDialog({
  open,
  onOpenChange,
  stocks,
  onSuccess,
}: BulkDeleteDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDeleting, setIsDeleting] = useState(false)

  const mutation = useMutation({
    mutationFn: async () => {
      // Delete all stocks in parallel
      await Promise.all(stocks.map((stock) => deleteStock(stock.symbol)))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] })
      toast({
        title: "Success",
        description: `Deleted ${stocks.length} stock${stocks.length > 1 ? "s" : ""} successfully`,
      })
      onOpenChange(false)
      setIsDeleting(false)
      onSuccess?.()
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to delete stocks",
        variant: "destructive",
      })
      setIsDeleting(false)
    },
  })

  const handleDelete = () => {
    setIsDeleting(true)
    mutation.mutate()
  }

  const stockSymbols = stocks.map((s) => s.symbol).join(", ")

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete {stocks.length} stock{stocks.length > 1 ? "s" : ""}?</AlertDialogTitle>
          <AlertDialogDescription>
            This will permanently delete the following stock{stocks.length > 1 ? "s" : ""} from your
            portfolio: <strong>{stockSymbols}</strong>. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? "Deleting..." : `Delete ${stocks.length} stock${stocks.length > 1 ? "s" : ""}`}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
