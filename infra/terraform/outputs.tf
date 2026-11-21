output "kubeconfig_path" {
  description = "Pfad zur erzeugten kubeconfig"
  value       = kind_cluster.this.kubeconfig_path
}

output "next_steps" {
  value = <<-EOT
    export KUBECONFIG=${kind_cluster.this.kubeconfig_path}
    kubectl -n hohe-warte get pods
    kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80   # admin / admin
    kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
  EOT
}
