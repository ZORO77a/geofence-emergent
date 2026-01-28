/**
 * File Service - Frontend
 * Handles all file operations: upload, download, list, view
 * Separates file management logic from UI components
 */

import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * File Service for managing file operations
 */
class FileService {
  constructor(token) {
    this.token = token;
    this.headers = { Authorization: `Bearer ${token}` };
  }

  /**
   * Upload a file
   * @param {File} file - File object from input
   * @returns {Promise<Object>} Upload response with file_id and timings
   */
  async uploadFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/files/upload`, formData, {
        headers: this.headers
      });

      return {
        success: true,
        data: response.data,
        message: 'File uploaded and encrypted'
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message,
        message: 'Failed to upload file'
      };
    }
  }

  /**
   * List all files
   * @param {Object} options - Query options
   * @param {number} options.latitude - Optional latitude
   * @param {number} options.longitude - Optional longitude
   * @param {string} options.wifi_ssid - Optional WiFi SSID
   * @returns {Promise<Array>} Array of file objects
   */
  async listFiles(options = {}) {
    try {
      const params = {};
      if (options.latitude !== undefined) params.latitude = options.latitude;
      if (options.longitude !== undefined) params.longitude = options.longitude;
      if (options.wifi_ssid) params.wifi_ssid = options.wifi_ssid;

      const response = await axios.get(`${API}/files`, {
        headers: this.headers,
        params
      });

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message,
        data: []
      };
    }
  }

  /**
   * Access/download a file
   * @param {string} fileId - ID of the file
   * @param {Object} options - Access options
   * @param {number} options.latitude - Latitude for geofence validation
   * @param {number} options.longitude - Longitude for geofence validation
   * @param {string} options.wifi_ssid - WiFi SSID for validation
   * @param {boolean} options.responseType - Response type (default: 'blob')
   * @returns {Promise<Blob>} File content as blob
   */
  async accessFile(fileId, options = {}) {
    try {
      const payload = {
        file_id: fileId,
        latitude: options.latitude,
        longitude: options.longitude,
        wifi_ssid: options.wifi_ssid
      };

      const response = await axios.post(`${API}/files/access`, payload, {
        headers: this.headers,
        responseType: options.responseType || 'blob'
      });

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      
      // Parse structured validation result if available
      if (typeof errorDetail === 'object') {
        return {
          success: false,
          error: errorDetail.reason || 'Access denied',
          validations: errorDetail.validations,
          status: error.response?.status
        };
      }

      return {
        success: false,
        error: errorDetail || error.message,
        status: error.response?.status
      };
    }
  }

  /**
   * Determine if file is accessible based on type
   * @param {string} filename - Name of the file
   * @returns {Object} File type information
   */
  getFileType(filename) {
    const nameLower = filename.toLowerCase();

    return {
      isImage: /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(nameLower),
      isPdf: nameLower.endsWith('.pdf'),
      isText: /\.(txt|md|log|json|csv)$/.test(nameLower),
      isSupported: true // All supported types above are viewable
    };
  }

  /**
   * Convert blob to text (for text files)
   * @param {Blob} blob - File blob
   * @returns {Promise<string>} File content as text
   */
  async blobToText(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsText(blob);
    });
  }

  /**
   * Convert blob to data URL (for images, PDFs)
   * @param {Blob} blob - File blob
   * @returns {Promise<string>} Data URL
   */
  async blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Create object URL for blob (alternative to data URL)
   * @param {Blob} blob - File blob
   * @returns {string} Object URL
   */
  createObjectUrl(blob) {
    return URL.createObjectURL(blob);
  }

  /**
   * Revoke object URL when done
   * @param {string} url - Object URL to revoke
   */
  revokeObjectUrl(url) {
    URL.revokeObjectURL(url);
  }

  /**
   * Download file to disk
   * @param {Blob} blob - File blob
   * @param {string} filename - Name for downloaded file
   */
  downloadFile(blob, filename) {
    const url = this.createObjectUrl(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    this.revokeObjectUrl(url);
  }

  /**
   * Get file size in human-readable format
   * @param {number} bytes - File size in bytes
   * @returns {string} Formatted size string
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Check if file is accessible based on file metadata
   * @param {Object} file - File metadata object
   * @returns {boolean} Whether file is accessible
   */
  isFileAccessible(file) {
    return file.accessible === true;
  }

  /**
   * Get access denial reason
   * @param {Object} file - File metadata object
   * @returns {string} Reason for access denial
   */
  getAccessReason(file) {
    return file.access_reason || 'Access denied';
  }

  /**
   * Validate file for upload
   * @param {File} file - File to validate
   * @param {Object} options - Validation options
   * @param {number} options.maxSizeBytes - Maximum file size in bytes (default: 100MB)
   * @returns {Object} Validation result
   */
  validateFileForUpload(file, options = {}) {
    const maxSize = options.maxSizeBytes || 100 * 1024 * 1024; // 100MB default

    if (!file) {
      return { valid: false, error: 'Please select a file' };
    }

    if (file.size > maxSize) {
      return { 
        valid: false, 
        error: `File size exceeds maximum of ${this.formatFileSize(maxSize)}` 
      };
    }

    return { valid: true };
  }
}

export default FileService;
