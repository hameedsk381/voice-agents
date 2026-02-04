export default function Footer() {
    return (
        <footer className="py-12 bg-black border-t border-white/10 text-gray-400 text-sm">
            <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-blue-600 rounded-md flex items-center justify-center text-white font-bold text-xs">V</div>
                    <span className="text-white font-semibold">OpenVoice Orchestrator</span>
                </div>

                <div className="flex gap-6">
                    <a href="#" className="hover:text-white transition-colors">Github</a>
                    <a href="#" className="hover:text-white transition-colors">Documentation</a>
                    <a href="#" className="hover:text-white transition-colors">Twitter</a>
                </div>

                <p>© 2026 OpenVoice Inc. Open Source MIT License.</p>
            </div>
        </footer>
    )
}
