use std::net::{IpAddr, SocketAddr};
use std::path::PathBuf;

use anyhow::Context;
use bijmantra_server::{AppState, serve};
use clap::Parser;
use tracing_subscriber::EnvFilter;

#[derive(Debug, Parser)]
#[command(name = "bijmantra-server")]
#[command(about = "BijMantra Rust API server")]
struct Args {
    #[arg(long, env = "BIJMANTRA_HOST", default_value = "127.0.0.1")]
    host: IpAddr,
    #[arg(long, env = "BIJMANTRA_PORT", default_value_t = 8000)]
    port: u16,
    #[arg(long, env = "BIJMANTRA_WORKSPACE", default_value = ".")]
    workspace: PathBuf,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .init();

    let args = Args::parse();
    let workspace = args
        .workspace
        .canonicalize()
        .with_context(|| format!("failed to resolve workspace {}", args.workspace.display()))?;
    let addr = SocketAddr::new(args.host, args.port);

    serve(addr, AppState::new(workspace)).await
}
