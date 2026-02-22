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

export interface DeleteStockDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  stock: Stock
  onSuccess?: () => void
}

export function DeleteStockDialog({
  open,
  onOpenChange,
  stock,
  onSuccess,
}: DeleteStockDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDeleting, setIsDeleting] = useState(false)

  const mutation = useMutation({
    mutationFn: () => deleteStock(stock.symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] })
      toast({
        title: "Success",
        description: `Stock ${stock.symbol} deleted successfully`,
      })
      onOpenChange(false)
      setIsDeleting(false)
      onSuccess?.()
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to delete stock",
        variant: "destructive",
      })
      setIsDeleting(false)
    },
  })

  const handleDelete = () => {
    setIsDeleting(true)
    mutation.mutate()
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This will permanently delete <strong>{stock.symbol}</strong> ({stock.name}) from your
            portfolio. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
