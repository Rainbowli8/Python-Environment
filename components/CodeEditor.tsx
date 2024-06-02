'use client'

import { useEffect, useState, useRef } from 'react'
import 'codemirror/lib/codemirror.css';
import 'codemirror/theme/material.css';

const CodeEditor: React.FC = () => {
    const codeMirrorRef = useRef(null);
    const editorInstanceRef = useRef<any>()
    const [output, setOutput] = useState<string>('');
    const [code, setCode] = useState<string>("print('Hello World')");

    // dynamically import codemirror/mode/python/python
    useEffect(() => {
        const loadCodeMirrorMode = async () => {
            if (typeof window !== 'undefined') {
                try {
                    await import('codemirror/mode/python/python');
                    console.log('CodeMirror Python mode loaded');
                } catch (error) {
                    console.error('Failed to load CodeMirror Python mode:', error);
                }
            }
        };

        const initializeCodeMirror = async () => {
            await loadCodeMirrorMode();
            const CodeMirror = require('codemirror');
            if (!editorInstanceRef.current && codeMirrorRef.current) {
                editorInstanceRef.current = CodeMirror.fromTextArea(codeMirrorRef.current, {
                    lineNumbers: true,
                    lineWrapping: true,
                    mode: 'python',
                    theme: 'material',
                });
                editorInstanceRef.current.setSize('100%', '100%');
                editorInstanceRef.current.on('change', (instance: any) => {
                    setCode(instance.getValue());
                });
            }
        };

        initializeCodeMirror();

        return () => {
            if (editorInstanceRef.current) {
                editorInstanceRef.current.toTextArea();
                editorInstanceRef.current = null;  // Clean up the editor instance
            }
        };
    }, []);

    const handleRunCode = async () => {
        try {
            const response = await fetch('http://localhost:8000/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: code }),
            });
            if (!response.ok) {
                const error = await response.json();
                setOutput(error.detail || 'An error occurred');
            } else {
                const result = await response.json();
                setOutput(result.output || result.error);
            }
        } catch (error) {
            setOutput('Failed to connect to the server.');
        }
    }

    const handleSubmit = async () => {
        try {
            const response = await fetch('http://localhost:8000/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: code }),
            });
            const result = await response.json();
            if (response.ok && !result.error) {
                // If the code runs successfully, store the code and output in formatted content
                const storeResponse = await fetch('http://localhost:8000/store/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: code, output: result.output }),
                });
                if (storeResponse.ok) {
                    alert('Code and output successfully saved!');
                } else {
                    alert('Failed to save code and output.');
                }
            } else {
                setOutput(result.error);
                alert('Code execution failed.');
            }
        } catch (error) {
            alert('Failed to connect to the server.');
        }
    };

    return (
        <div className="flex flex-col items-center min-h-screen w-full h-full p-4 bg-gray-100">
            <h1 className="text-2xl font-bold mb-4">PYTHON EXECUTION ENVIRONMENT</h1>
            <div className="flex w-full h-full flex-1 space-x-4">
                <section className="flex-1 h-100">
                    <textarea ref={codeMirrorRef} defaultValue={code}>
                    </textarea>
                </section>
                <div className="flex-1 border-2 border-green-500 bg-white p-4">
                    <p className="text-center text-lg font-semibold text-gray-700">Output</p>
                    <pre className="bg-gray-100 p-4 overflow-auto text-gray-800" style={{ maxHeight: '50rem' }}>{output}</pre>
                </div>
            </div>
            <div className="flex justify-between w-full mt-4">
                <button className="p-2 bg-red-500 text-white rounded" onClick={handleRunCode}>
                    Run Code
                </button>
                <button className="p-2 bg-green-500 text-white rounded" onClick={handleSubmit}>
                    Submit
                </button>
            </div>
        </div>
    );
};

export default CodeEditor;
