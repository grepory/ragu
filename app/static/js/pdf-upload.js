// React component for PDF upload with drag-and-drop functionality

// PDFUpload component
const PDFUpload = () => {
    // State for managing uploaded files and UI states
    const [files, setFiles] = React.useState([]);
    const [isDragging, setIsDragging] = React.useState(false);
    const [isUploading, setIsUploading] = React.useState(false);
    const [uploadStatus, setUploadStatus] = React.useState(null);
    const [collections, setCollections] = React.useState([]);
    const [selectedCollection, setSelectedCollection] = React.useState('');
    const [tags, setTags] = React.useState('');
    
    // Ref for file input
    const fileInputRef = React.useRef(null);
    
    // Fetch collections on component mount
    React.useEffect(() => {
        fetchCollections();
    }, []);
    
    // Fetch collections from API
    const fetchCollections = async () => {
        try {
            const response = await fetch('/api/v1/collections/');
            if (response.ok) {
                const data = await response.json();
                setCollections(data.collections || []);
                if (data.collections && data.collections.length > 0) {
                    setSelectedCollection(data.collections[0]);
                }
            } else {
                console.error('Failed to fetch collections');
            }
        } catch (error) {
            console.error('Error fetching collections:', error);
        }
    };
    
    // Handle drag events
    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };
    
    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };
    
    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!isDragging) {
            setIsDragging(true);
        }
    };
    
    // Handle drop event
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        
        const droppedFiles = Array.from(e.dataTransfer.files);
        handleFiles(droppedFiles);
    };
    
    // Handle file input change
    const handleFileInputChange = (e) => {
        const selectedFiles = Array.from(e.target.files);
        handleFiles(selectedFiles);
    };
    
    // Process and validate files
    const handleFiles = (newFiles) => {
        // Filter for PDF files only
        const pdfFiles = newFiles.filter(file => 
            file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        );
        
        if (pdfFiles.length === 0) {
            setUploadStatus({
                success: false,
                message: 'Only PDF files are allowed.'
            });
            return;
        }
        
        // Add new files to state
        setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
        setUploadStatus(null);
        
        // Reset file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };
    
    // Remove file from list
    const removeFile = (index) => {
        setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
    };
    
    // Handle click on upload area
    const handleUploadAreaClick = () => {
        fileInputRef.current.click();
    };
    
    // Handle collection change
    const handleCollectionChange = (e) => {
        setSelectedCollection(e.target.value);
    };
    
    // Handle tags change
    const handleTagsChange = (e) => {
        setTags(e.target.value);
    };
    
    // Upload files to server
    const uploadFiles = async () => {
        if (files.length === 0) {
            setUploadStatus({
                success: false,
                message: 'Please select at least one PDF file to upload.'
            });
            return;
        }
        
        if (!selectedCollection) {
            setUploadStatus({
                success: false,
                message: 'Please select a collection.'
            });
            return;
        }
        
        setIsUploading(true);
        setUploadStatus(null);
        
        try {
            // Upload each file
            const results = await Promise.all(files.map(async (file) => {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('collection_name', selectedCollection);
                
                if (tags) {
                    formData.append('tags', tags);
                }
                
                const response = await fetch('/api/v1/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                return {
                    fileName: file.name,
                    success: response.ok,
                    message: response.ok ? result.message : result.detail || 'Upload failed'
                };
            }));
            
            // Check if all uploads were successful
            const allSuccessful = results.every(result => result.success);
            
            setUploadStatus({
                success: allSuccessful,
                message: allSuccessful 
                    ? `Successfully uploaded ${results.length} file(s).`
                    : 'Some files failed to upload. See details below.',
                details: results
            });
            
            // Clear files if all uploads were successful
            if (allSuccessful) {
                setFiles([]);
            }
        } catch (error) {
            console.error('Error uploading files:', error);
            setUploadStatus({
                success: false,
                message: `Error uploading files: ${error.message}`
            });
        } finally {
            setIsUploading(false);
        }
    };
    
    // Create a new collection
    const createCollection = async () => {
        const collectionName = prompt('Enter a name for the new collection:');
        if (!collectionName) return;
        
        try {
            const response = await fetch('/api/v1/collections/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: collectionName,
                    description: `Collection created on ${new Date().toLocaleString()}`
                })
            });
            
            if (response.ok) {
                await fetchCollections();
                setSelectedCollection(collectionName);
            } else {
                const error = await response.json();
                alert(`Failed to create collection: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error creating collection:', error);
            alert(`Error creating collection: ${error.message}`);
        }
    };
    
    return (
        <div className="pdf-upload-component">
            <h3>Upload PDF Documents</h3>
            
            {/* Collection selection */}
            <div className="mb-3">
                <label htmlFor="collection-select" className="form-label">Collection</label>
                <div className="input-group">
                    <select 
                        id="collection-select"
                        className="form-select"
                        value={selectedCollection}
                        onChange={handleCollectionChange}
                    >
                        <option value="">Select a collection</option>
                        {collections.map(collection => (
                            <option key={collection} value={collection}>
                                {collection}
                            </option>
                        ))}
                    </select>
                    <button 
                        className="btn btn-outline-secondary" 
                        type="button"
                        onClick={createCollection}
                    >
                        New
                    </button>
                </div>
            </div>
            
            {/* Tags input */}
            <div className="mb-3">
                <label htmlFor="tags-input" className="form-label">Tags (comma-separated)</label>
                <input
                    type="text"
                    id="tags-input"
                    className="form-control"
                    placeholder="e.g., important, report, financial"
                    value={tags}
                    onChange={handleTagsChange}
                />
            </div>
            
            {/* Drag and drop area */}
            <div 
                className={`pdf-upload-area mb-3 ${isDragging ? 'drag-active' : ''}`}
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleUploadAreaClick}
            >
                <div className="pdf-upload-icon">
                    <i className="bi bi-file-earmark-pdf fs-1"></i>
                </div>
                <div className="pdf-upload-text">
                    <p>Drag & drop PDF files here or click to browse</p>
                </div>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileInputChange}
                    accept=".pdf,application/pdf"
                    multiple
                    style={{ display: 'none' }}
                />
            </div>
            
            {/* File list */}
            {files.length > 0 && (
                <div className="pdf-file-list mb-3">
                    <h5>Selected Files ({files.length})</h5>
                    <ul className="list-group">
                        {files.map((file, index) => (
                            <li key={index} className="list-group-item pdf-file-item">
                                <span className="pdf-file-name">{file.name}</span>
                                <span 
                                    className="pdf-file-remove"
                                    onClick={() => removeFile(index)}
                                >
                                    <i className="bi bi-x-circle"></i>
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            
            {/* Upload button */}
            <button 
                className="btn btn-primary"
                onClick={uploadFiles}
                disabled={isUploading || files.length === 0 || !selectedCollection}
            >
                {isUploading ? (
                    <>
                        <span className="loading-spinner me-2"></span>
                        Processing with OCR...
                    </>
                ) : 'Upload Files'}
            </button>
            
            {/* Upload status */}
            {uploadStatus && (
                <div className={`alert mt-3 ${uploadStatus.success ? 'alert-success' : 'alert-danger'}`}>
                    <p>{uploadStatus.message}</p>
                    {uploadStatus.details && (
                        <ul className="mb-0">
                            {uploadStatus.details.map((detail, index) => (
                                <li key={index}>
                                    {detail.fileName}: {detail.success ? '✓' : '✗'} {!detail.success && detail.message}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
        </div>
    );
};

// Render the component
ReactDOM.render(
    <PDFUpload />,
    document.getElementById('pdf-upload-container')
);