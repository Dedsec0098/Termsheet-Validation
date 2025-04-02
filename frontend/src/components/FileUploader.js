import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, Alert } from 'react-bootstrap';

const FileUploader = ({ label, helpText, acceptedFiles, onFileAccepted }) => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);

 // Update the onDrop function in FileUploader.js

 const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles && rejectedFiles.length > 0) {
      console.error("Rejected files:", rejectedFiles);
      setError('Please upload a valid file type.');
      return;
    }
  
    if (acceptedFiles && acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      console.log("Accepted file:", selectedFile);
      console.log("File details:", {
        name: selectedFile.name,
        type: selectedFile.type,
        size: selectedFile.size,
        lastModified: selectedFile.lastModified
      });
      
      // Check if file has a name and extension
      if (!selectedFile.name || !selectedFile.name.includes('.')) {
        setError('File must have a valid extension (.pdf, .docx, .xlsx, etc.)');
        return;
      }
      
      setFile(selectedFile);
      setError(null);
      onFileAccepted(selectedFile);
    }
  }, [onFileAccepted]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFiles.reduce((acc, curr) => {
      const mimeType = curr === '.pdf' ? { 'application/pdf': [] } :
                       curr === '.docx' ? { 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [] } :
                       curr === '.xlsx' ? { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [] } :
                       curr === '.csv' ? { 'text/csv': [] } :
                       curr === '.jpg' || curr === '.jpeg' ? { 'image/jpeg': [] } :
                       curr === '.png' ? { 'image/png': [] } :
                       curr === '.tif' || curr === '.tiff' ? { 'image/tiff': [] } : {};
      return { ...acc, ...mimeType };
    }, {}),
    maxFiles: 1
  });

  return (
    <Card className="file-upload-container">
      <Card.Header as="h5">{label}</Card.Header>
      <Card.Body>
        <div 
          {...getRootProps()} 
          className={`file-upload-area ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          {
            isDragActive ?
              <p>Drop the file here...</p> :
              <p>Drag & drop a file here, or click to select a file</p>
          }
          <p className="mt-2 small text-muted">{helpText}</p>
          <p className="mt-1 small text-muted">
            Accepted file types: {acceptedFiles.join(', ')}
          </p>
        </div>
        
        {error && (
          <Alert variant="danger" className="mt-2">
            {error}
          </Alert>
        )}
        
        {file && (
          <div className="file-details mt-3">
            <p><strong>Selected file:</strong> {file.name}</p>
            <p><strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB</p>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default FileUploader;