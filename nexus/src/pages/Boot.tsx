import "./Boot.css";

export default function Boot() {
    return (
        <div className="boot-screen">
            <div className="boot-center">
                <div className="boot-logo">NEXUS</div>

                <div className="boot-sub">
                    Initializing intelligent workspace
                </div>

                <div className="boot-loader">
                    <span />
                    <span />
                    <span />
                </div>
            </div>
        </div>
    );
}
