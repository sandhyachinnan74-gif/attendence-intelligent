import { api } from '../services/api';

/**
 * Downloads a file from an authenticated API endpoint as a blob.
 * Automatically injects JWT Bearer token and triggers a browser file download.
 */
export const downloadFile = async (
  endpointUrl: string,
  fallbackFilename: string,
  onStart?: () => void,
  onFinish?: () => void
): Promise<boolean> => {
  if (onStart) onStart();
  try {
    const response = await api.get(endpointUrl, {
      responseType: 'blob',
    });

    // Try extracting filename from Content-Disposition header
    let filename = fallbackFilename;
    const disposition = (response.headers['content-disposition'] || response.headers['Content-Disposition']) as string | undefined;
    if (disposition && typeof disposition === 'string') {
      const filenameMatch = disposition.match(/filename=["']?([^"';]+)["']?/i);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].trim();
      }
    }

    const contentType = (response.headers['content-type'] as string) || 'application/octet-stream';
    const blob = new Blob([response.data], { type: contentType });
    const downloadUrl = window.URL.createObjectURL(blob);
    const tempLink = document.createElement('a');
    tempLink.href = downloadUrl;
    tempLink.setAttribute('download', filename);
    document.body.appendChild(tempLink);
    tempLink.click();
    document.body.removeChild(tempLink);
    window.URL.revokeObjectURL(downloadUrl);
    return true;
  } catch (error: any) {
    console.error('File export error:', error);
    const errorDetail = error.response?.data?.detail || 'Failed to download file. Please ensure you are authorized.';
    alert(`Export Error: ${errorDetail}`);
    return false;
  } finally {
    if (onFinish) onFinish();
  }
};
