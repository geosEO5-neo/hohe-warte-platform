terraform {
  required_version = ">= 1.6.0"
  required_providers {
    kind       = { source = "tehcyx/kind", version = "~> 0.13" }
    helm       = { source = "hashicorp/helm", version = "~> 2.16" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.33" }
    null       = { source = "hashicorp/null", version = "~> 3.2" }
  }
}
