// Global type declarations for the project

// Declare node modules
declare module 'axios';
declare module 'dotenv';
declare module '@modelcontextprotocol/sdk/server' {
    export class Server {
        constructor(info: any, capabilities: any);
        onerror: (error: unknown) => void;
        close(): Promise<void>;
        setRequestHandler(schema: any, handler: (request: any) => Promise<any>): void;
        connect(transport: any): Promise<void>;
    }
}
declare module '@modelcontextprotocol/sdk/server/stdio';
declare module '@modelcontextprotocol/sdk/types';

// Declare global variables
declare var process: {
    env: {
        [key: string]: string | undefined;
    };
    on(event: string, listener: (...args: any[]) => void): void;
    exit(code?: number): void;
};
