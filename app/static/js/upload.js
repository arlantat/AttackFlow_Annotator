pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.9.359/pdf.worker.js';

let annotationCounter = 0; // Define a global counter for annotations
var localAnnotations = [];

// ---------- Viewer Initialization Functions ----------

function initializePDFViewer(url) {
    
    if (!url) return; // If no URL is provided, simply return
    const container = document.getElementById('pdf-pages');
    container.innerText = '';


    let pdfDoc = null;
    function renderPage(num, pdfDoc) {
        console.log("Rendering page: ", num);

        // Get the desired page
        pdfDoc.getPage(num).then(function (page) {
            const scale = 1.5;
            const viewport = page.getViewport({ scale: scale });

            // Prepare canvas using PDF page dimensions
            const canvas = document.createElement("canvas");
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            // Append the canvas to the PDF container
            const container = document.getElementById('pdf-pages');
            container.appendChild(canvas);

            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            // Render the page
            page.render(renderContext);

        });

    }

    console.log("Showing PDF for URL: ", url);
    pdfjsLib.getDocument(url).promise.then(function (pdfDoc_) {
        pdfDoc = pdfDoc_;

        // Display each page
        for (let i = 1; i <= pdfDoc.numPages; i++) {
            renderPage(i, pdfDoc);
        }
    });
}

function initializeWordViewer(url) {
    if (!url) return;

    const container = document.getElementById('pdf-pages');
    container.innerText = '';


    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('File not found or not a valid .docx format');
            }
            return response.blob();
        })
        .then(blob => {
            mammoth.convertToHtml({ arrayBuffer: blob })
                .then(result => {
                    container.innerHTML = result.value;
                })
                .catch(error => {
                    throw error; // re-throw the error to handle it in the next catch block
                });
        })
        .catch(error => {
            console.error('Error:', error.message);
            container.innerHTML = '<span style="color: red;">Failed to load Word document. File might not exist or is not a valid format.</span>';
        });

}


// ---------- Server Communication Functions ----------

function saveFile(event) {
    event.preventDefault();

    var filename = document.getElementById("filename").value;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/save", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);

            var saveMessageElement = document.getElementById("saveMessage");
            saveMessageElement.textContent = response.message;

            if (response.status == "success") {
                saveMessageElement.style.color = "green"; // Color the message green for success
            } else {
                saveMessageElement.style.color = "red"; // Color the message red for errors
            }
        }
    };
    xhr.send("filename=" + filename);
}

function createProject(event) {
    event.preventDefault();

    var formData = new FormData();
    formData.append('projectname', document.getElementById("projectname").value);
    formData.append('initialfile', document.getElementById("initialfile").files[0]);

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/create_project", true);
    xhr.onreadystatechange = function() {
        var messageElement = document.getElementById("projectCreationMessage");
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            messageElement.textContent = response.message;
            if (response.status == "success") {
                loadProjects();
                messageElement.style.color = "green"; 
            } else {
                messageElement.style.color = "red"; 
            }
        }
    };
    xhr.send(formData);
}

function loadProjects() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/projects", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            var projectListElement = document.getElementById("projectList");
            projectListElement.innerHTML = "";

            // Populate projects
            response.projects.forEach(function(project) {
                var listItem = document.createElement("li");
                
                var projectButton = document.createElement("button");
                projectButton.textContent = project.project_name;
                projectButton.onclick = function() {
                    clearAction();
                    console.log("Loading project: ", project._id);
                    document.getElementById("actionButtons").style.display = "none";
                    document.getElementById("versionList").style.display = "block";
                    displayVersions(project._id);
                };
                
                var deleteButton = document.createElement("button");
                deleteButton.textContent = "Delete";
                deleteButton.id = "deleteButton";
                deleteButton.onclick = function() {
                    delete_project(project._id);
                };

                listItem.appendChild(projectButton);
                listItem.appendChild(deleteButton);
                projectListElement.appendChild(listItem);
            });
        }
    };
    xhr.send();
}

function displayVersions(projectId) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/project_versions/" + projectId, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            var versionListElement = document.getElementById("versionList");
            
            document.getElementById("versionsDetails").open = true;
            versionListElement.innerHTML = "";  

            response.versions.forEach(function(version) {
                
                var versionItem = document.createElement("li");
            
                var versionLabel = document.createElement("span");
                versionLabel.textContent = "Version Date: " + version.version_date;
                versionItem.appendChild(versionLabel);
            
                var loadButton = document.createElement("button");
                loadButton.textContent = "Load";
                loadButton.onclick = function() {
                    
                    htmlContainer = document.getElementById("html-pages");
                    htmlContainer.innerHTML = '';
                    
                    document.getElementById("actionButtons").style.display = "block";
                    loadFileFromDB(version.file_id);
                    resetAnnotationsContainer();
                };
                versionItem.appendChild(loadButton);
            
                var deleteButton = document.createElement("button");
                deleteButton.textContent = "Delete";
                deleteButton.id = "deleteButton";
                deleteButton.onclick = function() {
                    document.getElementById("actionButtons").style.display = "block";
                    deleteFileFromDB(version.file_id);
                };
                versionItem.appendChild(deleteButton);
            
                document.getElementById("versionList").appendChild(versionItem);
            });
            
        }
    };
    xhr.send();
}

function loadFileFromDB(file_id) {
    localAnnotations = [];
    annotationCounter = 0;
    fetch(`/load_from_mongo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `file_id=${file_id}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch the file');
        }
        return response.json();
    })
    .then(data => {
        // clear the annotations container
        resetAnnotationsContainer();

        const pdfContainer = document.getElementById("pdf-pages");
        console.log("Loading file: ", data.filetype);
        if (data.filetype === "pdf") {
            initializePDFViewer(data.url);
        } else if (data.filetype === "docx") {
            initializeWordViewer(data.url);
        } else if (data.filetype === "html") {
            console.log("HTML content:", data.content);
            pdfContainer.innerHTML = data.content;
          
            // Set the local annotations from the retrieved data
            localAnnotations = data.annotations;

            // Populate the annotationsContainer with loaded annotations
            localAnnotations.forEach(annotation => {
                addVisualRepresentationToAnnotationsContainer(annotation);
            });

            // set the annotation counter
            if (localAnnotations.length > 0) {
                annotationCounter = Math.max(...localAnnotations.map(annotation => annotation.annotation_id));
            }
        } else {
            console.error("Unsupported file type");
        }
    })
    .catch(error => {
        const loadMessage = document.getElementById("loadMessage");
        loadMessage.textContent = "Failed to load content!";
        console.error("Error loading content:", error.message);
    });

    // Hide the annotations container
    const annotationsContainer = document.getElementById('annotationsContainer');
    annotationsContainer.style.display = 'none'; // Hide the annotations container
}

function deleteFileFromDB(file_id) {
    fetch(`/delete_file`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `file_id=${file_id}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("File deleted successfully!");
            if (data.project_id) {
                displayVersions(data.project_id);
            } else {
                alert("File was deleted, but project ID was not received.");
            }
        } else {
            alert("Failed to delete file: " + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Failed to communicate with the server.");
    });
}

function delete_project(project_id) {
    fetch('/delete_project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `project_id=${project_id}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Project deleted successfully!");
            loadProjects();
        } else {
            alert("Failed to delete project: " + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Failed to communicate with the server.");
    });
}


// ---------- Clear page & annoate button ----------

document.addEventListener("DOMContentLoaded", () => {
    
    const clearBtn = document.getElementById("clearBtn");
    const annotate = document.getElementById("annotate");
    // const updateButton = document.getElementById("updatebutton");

    if (clearBtn) {
        clearBtn.addEventListener("click", clearAction);
    }

    if (annotate) {
        annotate.addEventListener("click", annotateAction);
    }

    // if (updateButton) {
    //     updateButton.addEventListener("click", updateAction);
    // }
    
    loadProjects();

    document.getElementById("projectsDetails").addEventListener("click", projectsDetailsAction);
});

function clearAction() {
    resetAnnotationsContainer();
    document.getElementById("actionButtons").style.display = "none";
    document.getElementById("versionList").style.display = "none";
    const pdfContainer = document.getElementById("pdf-pages");
    const htmlContainer = document.getElementById("html-pages");
    if (pdfContainer) {
        pdfContainer.innerHTML = '';
        htmlContainer.innerHTML = '';
    }

    fetch('/clear_temp', { method: 'POST' })
        .then(response => response.json())
        .then(data => console.log(data.message))
        .catch(error => console.error('Clearing Error:', error));
}

function annotateAction() {
    fetch('/session_file_info', { method: 'GET' })
        .then(response => response.json())
        .then(fileInfo => {
            console.log('File info:', fileInfo);
            const pdfContainer = document.getElementById("pdf-pages");
            const htmlContainer = document.getElementById("html-pages");
            
            if (!pdfContainer || !htmlContainer) {
                console.error('Error accessing the containers');
                return;
            }

            if (fileInfo.filetype === '.docx' || fileInfo.filetype === '.html') {
                // If it's a docx or html, copy the content from pdf-container to html-container
                htmlContainer.innerHTML = pdfContainer.innerHTML;
            } else if (fileInfo.filetype === '.pdf') {
                // If it's a PDF, send request to convert the PDF to HTML
                fetch('/annotate', { method: 'POST' })
                    .then(response => response.text())
                    .then(htmlContent => {
                        htmlContainer.innerHTML = htmlContent;
                    })
                    .catch(error => console.error('Conversion Error:', error));
            } else {
                console.error('Unsupported file type:', fileInfo.filetype);
            }
        })
        .catch(error => console.error('Error fetching session file info:', error));

    // Display the annotations container
    const annotationsContainer = document.getElementById('annotationsContainer');
    annotationsContainer.style.display = 'block'; // Show the annotations container
}

function projectsDetailsAction() {
    const versionsDetails = document.getElementById("versionsDetails");
    if (this.open) {
        versionsDetails.open = false;
        loadProjects();
    }
}


// ---------- Annotation Functions  ----------

annotations = [
    ['Reconnaissance','TA0043'],
    ['Resource Development','TA0042'],
    ['Initial Access','TA0001'],
    ['Execution','TA0002'],
    ['Persistence','TA0003'],
    ['Privilege Escalation','TA0004'],
    ['Defense Evasion','TA0005'],
    ['Credential Access','TA0006'],
    ['Discovery','TA0007'],
    ['Lateral Movement','TA0008'],
    ['Collection','TA0009'],
    ['Command and Control','TA0011'],
    ['Exfiltration','TA0010'],
    ['Impact','TA0040']
];

document.addEventListener("DOMContentLoaded", function() {
    const dropdown = document.getElementById('annotationDropdown');

    annotations.forEach(annotation => {
        const option = document.createElement('option');
        option.value = `${annotation[0]}:${annotation[1]}`;
        option.innerText = annotation[0];
        dropdown.appendChild(option);
    });
});

document.addEventListener('mouseup', function(event) {
    const selectedText = window.getSelection().toString().trim();
    const annotationControls = document.getElementById('annotationControls');

    // Check if the selection is within the html-pages container
    let isInHtmlPages = false;
    let node = window.getSelection().anchorNode;
    while (node != null) {
        if (node.id === "html-pages") {
            isInHtmlPages = true;
            break;
        }
        node = node.parentNode;
    }

    if (selectedText.length > 0 && isInHtmlPages) {
        annotationControls.style.display = 'block';
    } else {
        annotationControls.style.display = 'none';
    }
});

function addAnnotation() {
    const selectedText = window.getSelection().toString().trim();
    const dropdown = document.getElementById('annotationDropdown');
    const selectedAnnotation = dropdown.value.split(":");
    const tag = selectedAnnotation[0];
    const tagCode = selectedAnnotation[1];
    annotationCounter++;  // Increment the counter for each new annotation

    localAnnotations.push({
        annotation_id: annotationCounter,
        selected_text: selectedText,
        tag: tag,
        code: tagCode,
        related_annotation_ids: []
    });

    addVisualRepresentationToAnnotationsContainer({
        annotation_id: annotationCounter,
        selected_text: selectedText,
        tag: tag,
        code: tagCode
    });

    // Highlighted text 
    const span = document.createElement('span');
    span.className = 'highlighted-text';
    span.dataset.tag = tag;  
    span.dataset.annotationId = annotationCounter;

    const range = window.getSelection().getRangeAt(0);
    range.surroundContents(span);
    window.getSelection().removeAllRanges();  // Deselect the text

    refreshAnnotationsDisplay();
}

function addVisualRepresentationToAnnotationsContainer(annotation) {
    const container = document.getElementById('annotationsContainer');
    
    // Check if the update button already exists
    let updateButton = container.querySelector('#updatebutton');
    
    // If it doesn't exist, create and append it to the top of the container
    if (!updateButton) {
        updateButton = document.createElement('input');
        updateButton.type = 'button';
        updateButton.value = 'Update';
        updateButton.id = 'updatebutton';
        updateButton.addEventListener('click', updateAction);
        container.prepend(updateButton);  // This ensures the button is at the top

        // Add headers
        const headers = document.createElement('div');
        headers.className = 'annotation-headers';
        headers.innerHTML = `
            <div>Tag ID</div>
            <div>Tag Name</div>
            <div>Related Tags</div>
        `;
        container.appendChild(headers);
    }

    // Create a new div for this annotation and append it to the container
    const annotationDiv = createAnnotationDiv(annotation);
    container.appendChild(annotationDiv);
}

function createAnnotationDiv(annotation) {
    const annotationDiv = document.createElement('div');
    annotationDiv.className = 'annotation';

    // Add ID
    annotationDiv.appendChild(createTagSpan(annotation));

    // Add tag name
    annotationDiv.appendChild(createTagNameSpan(annotation));

    // Add related annotations section
    annotationDiv.appendChild(createRelatedSection(annotation));

    // Add a remove button
    annotationDiv.appendChild(createRemoveButton(annotation));

    return annotationDiv;
}

function createTagSpan(annotation) {
    const tagIdSpan = document.createElement('span');
    tagIdSpan.textContent = `${annotation.annotation_id}`;
    tagIdSpan.style.width = '66px'; 
    return tagIdSpan;
}

function createTagNameSpan(annotation) {
    const tagNameSpan = document.createElement('span');
    tagNameSpan.textContent = `${annotation.tag}`;
    tagNameSpan.style.width = '150px'; 
    return tagNameSpan;
}

function createRelatedSection(annotation) {
    const relatedSectionWrapper = document.createElement('div');
    relatedSectionWrapper.className = 'related-section-wrapper';

    const relatedSection = document.createElement('div');
    relatedSection.className = 'related-section';

    localAnnotations.forEach(anno => {
        if (anno.annotation_id !== annotation.annotation_id) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = anno.annotation_id;
            checkbox.id = `relation-${annotation.annotation_id}-${anno.annotation_id}`;

            if (annotation.related_annotation_ids && 
                annotation.related_annotation_ids.includes(anno.annotation_id)) {
                checkbox.checked = true;
            }

            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = anno.annotation_id;

            relatedSection.appendChild(checkbox);
            relatedSection.appendChild(label);
        }
    });

    relatedSectionWrapper.appendChild(relatedSection);
    return relatedSectionWrapper;
}

function createRemoveButton(annotation) {
    const removeButton = document.createElement('button');
    removeButton.textContent = 'Remove';
    removeButton.addEventListener('click', function() {
        this.parentElement.parentElement.removeChild(this.parentElement);
        const index = localAnnotations.findIndex(anno => anno.annotation_id === annotation.annotation_id);
        if (index > -1) {
            localAnnotations.splice(index, 1);
        }
        removeHighlightedTextById(annotation.annotation_id);
    });
    return removeButton;
}

function updateRelatedAnnotationsBasedOnCheckboxes() {
    const container = document.getElementById('annotationsContainer');
    const annotationDivs = container.querySelectorAll('.annotation');

    annotationDivs.forEach(annotationDiv => {
        const annotationId = parseInt(annotationDiv.querySelector('span').textContent.split('-')[0].trim());
        const checkboxes = annotationDiv.querySelectorAll('input[type="checkbox"]');
        const checkedValues = Array.from(checkboxes).filter(checkbox => checkbox.checked).map(checkbox => parseInt(checkbox.value));

        const annotationIndex = localAnnotations.findIndex(anno => anno.annotation_id === annotationId);
        if (annotationIndex > -1) {
            localAnnotations[annotationIndex].related_annotation_ids = checkedValues;
        }
    });
}

function resetAnnotationsContainer() {
    // clears the visual annotations container
    const container = document.getElementById('annotationsContainer');
    container.innerHTML = '';
}

function refreshAnnotationsDisplay() {
    const container = document.getElementById('annotationsContainer');
    container.innerHTML = ''; // Clear the container
    
    localAnnotations.forEach(annotation => {
        addVisualRepresentationToAnnotationsContainer(annotation);
    });
}

function removeHighlightedTextById(annotationId) {
    const highlightedElements = document.querySelectorAll('.highlighted-text');
    highlightedElements.forEach(element => {
        if (element.dataset.annotationId == annotationId) {
            // Convert the span back to a text node and replace it
            const textNode = document.createTextNode(element.textContent);
            element.parentNode.replaceChild(textNode, element);
        }
    });
}

function updateAction() {
    updateRelatedAnnotationsBasedOnCheckboxes();
    const updatedHtmlContent = document.getElementById("html-pages").innerHTML;

    fetch('/update_project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            updatedHtml: updatedHtmlContent,
            annotations: localAnnotations  // Send the local annotations
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            alert("Updated successfully!");
            if (data.project_id) {
                displayVersions(data.project_id);
            } else {
                alert("Update was successful, but project ID was not received.");
            }
        } else {
            alert("Update failed!");
        }
    })
    .catch(error => console.error('Update Error:', error));
}




// ---------- Functions for debugging ----------

function displaySessionInfo() {
    fetch('/session_file_info')
        .then(response => response.json())
        .then(data => {
            console.log('Session Info:', data);

            // Modify the data values to be "Empty" if they are null
            for (let key in data) {
                if (data[key] === null) {
                    data[key] = 'Empty';
                }
            }

            const infoElement = document.getElementById('sessionInfoDisplay');
            infoElement.textContent = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            console.error('Error fetching session info:', error);
        });
}

function delayedDisplaySessionInfo() {
    setTimeout(displaySessionInfo, 100);
}

document.addEventListener('DOMContentLoaded', () => {
    displaySessionInfo();

    // Listener for input changes
    document.addEventListener('input', delayedDisplaySessionInfo);

    // Listener for clicks
    document.addEventListener('click', (event) => {
        // Check if the clicked element is a button or any other clickable element you want to track
        if (event.target.tagName === 'BUTTON' || event.target.tagName === 'A' || event.target.type === 'submit') {
            delayedDisplaySessionInfo();
        }
    });
});

function clearDatabase() {
    fetch('/clear_database', {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        const statusElement = document.getElementById("clearStatus");
        if (data.success) {
            loadProjects();
            statusElement.textContent = "Database cleared successfully!";
            
        } else {
            statusElement.textContent = "Error clearing database.";
        }
    })
    .catch(error => {
        console.error('Error clearing the database:', error);
        alert("Failed to communicate with the server.");
    });
}

