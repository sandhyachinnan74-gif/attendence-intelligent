import { api, API_BASE } from '../services/api';

/**
 * Downloads a file from an authenticated API endpoint as a blob.
 * Automatically handles URL prefixing, injects JWT Bearer token,
 * prevents instant object URL revocation, and falls back to direct
 * authenticated stream download if blob generation is blocked.
 */
export const downloadFile = async (
  endpointUrl: string,
  fallbackFilename: string,
  onStart?: () => void,
  onFinish?: () => void,
  onError?: (err: string) => void
): Promise<boolean> => {
  if (onStart) onStart();

  const token = localStorage.getItem('attendai_token') || localStorage.getItem('token') || '';

  // 1. Normalize endpoint URL:
  // Strip '/api/v1' prefix if present so axios baseURL handles it
  let cleanUrl = endpointUrl;
  if (cleanUrl.startsWith(`${API_BASE}/`)) {
    cleanUrl = cleanUrl.substring(API_BASE.length);
  } else if (cleanUrl.startsWith(API_BASE)) {
    cleanUrl = cleanUrl.substring(API_BASE.length);
  } else if (cleanUrl.startsWith('/api/v1/')) {
    cleanUrl = cleanUrl.substring('/api/v1'.length);
  } else if (cleanUrl.startsWith('/api/v1')) {
    cleanUrl = cleanUrl.substring('/api/v1'.length);
  }

  // Ensure query param token is also present as a safety fallback
  const urlWithToken = token && !cleanUrl.includes('token=')
    ? `${cleanUrl}${cleanUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
    : cleanUrl;

  try {
    const response = await api.get(cleanUrl, {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    // Check if response is actually a JSON error response wrapped in blob
    const contentType = (response.headers['content-type'] as string) || '';
    if (contentType.includes('application/json') || response.data.type === 'application/json') {
      const text = await response.data.text();
      let errorMsg = 'Failed to download file.';
      try {
        const json = JSON.parse(text);
        if (json.detail) errorMsg = json.detail;
      } catch (_) {}
      throw new Error(errorMsg);
    }

    // Extract filename from Content-Disposition header
    let filename = fallbackFilename;
    const disposition = (response.headers['content-disposition'] || response.headers['Content-Disposition']) as string | undefined;
    if (disposition && typeof disposition === 'string') {
      const filenameMatch = disposition.match(/filename=["']?([^"';]+)["']?/i);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].trim();
      }
    }

    const blobType = contentType || 'application/octet-stream';
    const blob = new Blob([response.data], { type: blobType });
    const downloadUrl = window.URL.createObjectURL(blob);

    const tempLink = document.createElement('a');
    tempLink.href = downloadUrl;
    tempLink.setAttribute('download', filename);
    tempLink.style.display = 'none';
    document.body.appendChild(tempLink);
    tempLink.click();

    // Do NOT synchronously revoke the URL immediately after click!
    // In Chrome/Edge, immediate revocation cancels or corrupts the in-flight download.
    setTimeout(() => {
      try {
        document.body.removeChild(tempLink);
        window.URL.revokeObjectURL(downloadUrl);
      } catch (_) {}
    }, 10000);

    return true;
  } catch (error: any) {
    console.error('File export error, attempting fallback download:', error);
    let errorDetail = 'Failed to download file. Please ensure you are authorized.';
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text();
        const json = JSON.parse(text);
        if (json.detail) errorDetail = json.detail;
      } catch (_) {}
    } else if (error.response?.data?.detail) {
      errorDetail = error.response.data.detail;
    } else if (error.message) {
      errorDetail = error.message;
    }

    // 2. Fallback: Trigger direct navigation download with query param token
    try {
      const fullFallbackUrl = `${API_BASE}${urlWithToken}`;
      const directLink = document.createElement('a');
      directLink.href = fullFallbackUrl;
      directLink.setAttribute('download', fallbackFilename);
      directLink.target = '_blank';
      directLink.style.display = 'none';
      document.body.appendChild(directLink);
      directLink.click();
      setTimeout(() => {
        try {
          document.body.removeChild(directLink);
        } catch (_) {}
      }, 5000);
      return true;
    } catch (fallbackError) {
      console.error('Direct download fallback failed:', fallbackError);
      if (onError) {
        onError(errorDetail);
      } else {
        window.dispatchEvent(new CustomEvent('attendai:notify', {
          detail: { message: `Export Error: ${errorDetail}`, type: 'error' }
        }));
      }
      return false;
    }
  } finally {
    if (onFinish) onFinish();
  }
};
