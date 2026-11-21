variable "cluster_name" {
  description = "Name des kind-Clusters"
  type        = string
  default     = "hohe-warte"
}

variable "kubernetes_version" {
  description = "kindest/node-Image-Tag (= Kubernetes-Version)"
  type        = string
  default     = "v1.36.4"
}

variable "worker_count" {
  description = "Anzahl der Worker-Nodes"
  type        = number
  default     = 2
  validation {
    condition     = var.worker_count >= 1 && var.worker_count <= 5
    error_message = "worker_count muss zwischen 1 und 5 liegen."
  }
}

variable "app_image" {
  description = "Lokal gebautes Image, das per 'kind load' in den Cluster geladen wird"
  type        = string
  default     = "hohe-warte:dev"
}

variable "install_monitoring" {
  description = "kube-prometheus-stack (Prometheus, Alertmanager, Grafana) installieren"
  type        = bool
  default     = true
}
