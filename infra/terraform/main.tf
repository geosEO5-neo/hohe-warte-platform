# Lokale, reproduzierbare Kubernetes-Plattform:
#   kind-Cluster (1 Control-Plane + N Worker)
#   -> kube-prometheus-stack (Monitoring/Alerting/Dashboards)
#   -> hohe-warte (Helm-Chart aus diesem Repo)
# Dasselbe Muster (Cluster-Modul + Helm-Releases) lässt sich auf Proxmox/vSphere-VMs
# oder einen Managed-Cluster übertragen, indem nur der Cluster-Provider getauscht wird.

resource "kind_cluster" "this" {
  name           = var.cluster_name
  node_image     = "kindest/node:${var.kubernetes_version}"
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
    }

    dynamic "node" {
      for_each = range(var.worker_count)
      content {
        role = "worker"
      }
    }
  }
}

provider "kubernetes" {
  host                   = kind_cluster.this.endpoint
  cluster_ca_certificate = kind_cluster.this.cluster_ca_certificate
  client_certificate     = kind_cluster.this.client_certificate
  client_key             = kind_cluster.this.client_key
}

provider "helm" {
  kubernetes {
    host                   = kind_cluster.this.endpoint
    cluster_ca_certificate = kind_cluster.this.cluster_ca_certificate
    client_certificate     = kind_cluster.this.client_certificate
    client_key             = kind_cluster.this.client_key
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

resource "kubernetes_namespace" "app" {
  metadata {
    name = "hohe-warte"
    labels = {
      "pod-security.kubernetes.io/enforce" = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "helm_release" "kube_prometheus_stack" {
  count      = var.install_monitoring ? 1 : 0
  name       = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "93.6.1"
  timeout    = 900
  wait       = true
  values     = [file("${path.module}/values/kube-prometheus-stack.yaml")]
}

# Image aus dem lokalen Docker-Daemon in alle kind-Nodes laden (kein Registry-Push nötig).
resource "null_resource" "load_image" {
  triggers = {
    cluster = kind_cluster.this.id
    image   = var.app_image
  }
  provisioner "local-exec" {
    command = "kind load docker-image ${var.app_image} --name ${var.cluster_name}"
  }
}

resource "helm_release" "hohe_warte" {
  name      = "hohe-warte"
  namespace = kubernetes_namespace.app.metadata[0].name
  chart     = "${path.module}/../../deploy/helm/hohe-warte"
  wait      = true
  timeout   = 300

  set {
    name  = "image.repository"
    value = split(":", var.app_image)[0]
  }
  set {
    name  = "image.tag"
    value = split(":", var.app_image)[1]
  }
  set {
    name  = "image.pullPolicy"
    value = "Never"
  }

  depends_on = [helm_release.kube_prometheus_stack, null_resource.load_image]
}
