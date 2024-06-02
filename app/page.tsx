import React from 'react';
import CodeEditor from '../components/CodeEditor';

const Home: React.FC = () => {
    return (
        <div className="w-full min-h-screen bg-gray-100">
            <main className="flex flex-col items-center justify-center w-full min-h-screen">
                <CodeEditor />
            </main>
        </div>
    );
};

export default Home;
