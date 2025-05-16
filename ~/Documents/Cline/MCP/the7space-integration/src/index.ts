#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ErrorCode,
    ListToolsRequestSchema,
    McpError,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Get API credentials from environment variables
const WP_API_URL = process.env.WP_API_URL;
const WP_USERNAME = process.env.WP_USERNAME;
const WP_APP_PASSWORD = process.env.WP_APP_PASSWORD;
const AMELIA_API_URL = process.env.AMELIA_API_URL || `${WP_API_URL}/wp-json/amelia/v1`;
const AMELIA_API_KEY = process.env.AMELIA_API_KEY;

// Validate required environment variables
if (!WP_API_URL || !WP_USERNAME || !WP_APP_PASSWORD) {
    throw new Error('WordPress API credentials are required (WP_API_URL, WP_USERNAME, WP_APP_PASSWORD)');
}

// Types for our integration
interface WPPost {
    id: number;
    title: {
        rendered: string;
    };
    content: {
        rendered: string;
    };
    slug: string;
    status: string;
    date: string;
    type: string;
}

interface AmeliaService {
    id: number;
    name: string;
    description?: string;
    color?: string;
    price: number;
    duration: number;
    categoryId?: number;
    minCapacity: number;
    maxCapacity: number;
    status: string;
}

interface AmeliaAppointment {
    id?: number;
    bookingStart: string;
    bookingEnd: string;
    status: string;
    serviceId: number;
    providerId: number;
    customerId?: number;
    customerFirstName: string;
    customerLastName: string;
    customerEmail: string;
    customerPhone?: string;
    locationId?: number;
    internalNotes?: string;
}

class The7SpaceIntegrationServer {
    private server: Server;
    private wpAxiosInstance;
    private ameliaAxiosInstance;

    constructor() {
        // Initialize the MCP server
        this.server = new Server(
            {
                name: 'the7space-integration-server',
                version: '0.1.0',
            },
            {
                capabilities: {
                    tools: {},
                },
            }
        );

        // Initialize WordPress API client
        this.wpAxiosInstance = axios.create({
            baseURL: `${WP_API_URL}/wp-json/wp/v2`,
            auth: {
                username: WP_USERNAME,
                password: WP_APP_PASSWORD,
            },
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Initialize Amelia API client (if credentials are available)
        if (AMELIA_API_URL && AMELIA_API_KEY) {
            this.ameliaAxiosInstance = axios.create({
                baseURL: AMELIA_API_URL,
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-KEY': AMELIA_API_KEY,
                },
            });
        }

        // Setup tool handlers
        this.setupToolHandlers();

        // Error handling
        this.server.onerror = (error) => console.error('[MCP Error]', error);
        process.on('SIGINT', async () => {
            await this.server.close();
            process.exit(0);
        });
    }

    private setupToolHandlers() {
        // List available tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                // WordPress Content Tools
                {
                    name: 'get_wp_posts',
                    description: 'Get WordPress posts with filtering options',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            post_type: {
                                type: 'string',
                                description: 'Post type (post, page, etc.)',
                                default: 'post',
                            },
                            status: {
                                type: 'string',
                                description: 'Post status (publish, draft, etc.)',
                                default: 'publish',
                            },
                            per_page: {
                                type: 'number',
                                description: 'Number of posts to retrieve',
                                default: 10,
                            },
                            page: {
                                type: 'number',
                                description: 'Page number',
                                default: 1,
                            },
                            search: {
                                type: 'string',
                                description: 'Search term',
                            },
                        },
                    },
                },
                {
                    name: 'create_wp_post',
                    description: 'Create a new WordPress post or page',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            title: {
                                type: 'string',
                                description: 'Post title',
                            },
                            content: {
                                type: 'string',
                                description: 'Post content',
                            },
                            post_type: {
                                type: 'string',
                                description: 'Post type (post, page, etc.)',
                                default: 'post',
                            },
                            status: {
                                type: 'string',
                                description: 'Post status (publish, draft, etc.)',
                                default: 'draft',
                            },
                            categories: {
                                type: 'array',
                                items: {
                                    type: 'number',
                                },
                                description: 'Category IDs',
                            },
                            tags: {
                                type: 'array',
                                items: {
                                    type: 'number',
                                },
                                description: 'Tag IDs',
                            },
                        },
                        required: ['title', 'content'],
                    },
                },
                {
                    name: 'update_wp_post',
                    description: 'Update an existing WordPress post or page',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            id: {
                                type: 'number',
                                description: 'Post ID',
                            },
                            title: {
                                type: 'string',
                                description: 'Post title',
                            },
                            content: {
                                type: 'string',
                                description: 'Post content',
                            },
                            status: {
                                type: 'string',
                                description: 'Post status (publish, draft, etc.)',
                            },
                            categories: {
                                type: 'array',
                                items: {
                                    type: 'number',
                                },
                                description: 'Category IDs',
                            },
                            tags: {
                                type: 'array',
                                items: {
                                    type: 'number',
                                },
                                description: 'Tag IDs',
                            },
                        },
                        required: ['id'],
                    },
                },
                // Elementor Pro Tools
                {
                    name: 'get_elementor_templates',
                    description: 'Get available Elementor templates',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            template_type: {
                                type: 'string',
                                description: 'Template type (page, section, etc.)',
                            },
                            per_page: {
                                type: 'number',
                                description: 'Number of templates to retrieve',
                                default: 10,
                            },
                        },
                    },
                },
                {
                    name: 'apply_elementor_template',
                    description: 'Apply an Elementor template to a page',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            page_id: {
                                type: 'number',
                                description: 'Page ID',
                            },
                            template_id: {
                                type: 'number',
                                description: 'Template ID',
                            },
                        },
                        required: ['page_id', 'template_id'],
                    },
                },
                // Amelia Booking Tools
                {
                    name: 'get_amelia_services',
                    description: 'Get available Amelia services',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            category_id: {
                                type: 'number',
                                description: 'Filter by category ID',
                            },
                            status: {
                                type: 'string',
                                description: 'Service status (visible, hidden, disabled)',
                                default: 'visible',
                            },
                        },
                    },
                },
                {
                    name: 'get_amelia_appointments',
                    description: 'Get Amelia appointments with filtering options',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            start_date: {
                                type: 'string',
                                description: 'Start date (YYYY-MM-DD)',
                            },
                            end_date: {
                                type: 'string',
                                description: 'End date (YYYY-MM-DD)',
                            },
                            status: {
                                type: 'string',
                                description: 'Appointment status (pending, approved, canceled, rejected)',
                            },
                            customer_email: {
                                type: 'string',
                                description: 'Filter by customer email',
                            },
                        },
                    },
                },
                {
                    name: 'create_amelia_appointment',
                    description: 'Create a new Amelia appointment',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            service_id: {
                                type: 'number',
                                description: 'Service ID',
                            },
                            provider_id: {
                                type: 'number',
                                description: 'Provider ID',
                            },
                            booking_start: {
                                type: 'string',
                                description: 'Booking start time (ISO format)',
                            },
                            customer_first_name: {
                                type: 'string',
                                description: 'Customer first name',
                            },
                            customer_last_name: {
                                type: 'string',
                                description: 'Customer last name',
                            },
                            customer_email: {
                                type: 'string',
                                description: 'Customer email',
                            },
                            customer_phone: {
                                type: 'string',
                                description: 'Customer phone',
                            },
                            internal_notes: {
                                type: 'string',
                                description: 'Internal notes',
                            },
                        },
                        required: ['service_id', 'provider_id', 'booking_start', 'customer_first_name', 'customer_last_name', 'customer_email'],
                    },
                },
            ],
        }));

        // Handle tool calls
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;

            try {
                // WordPress Content Tools
                if (name === 'get_wp_posts') {
                    return await this.getWpPosts(args);
                } else if (name === 'create_wp_post') {
                    return await this.createWpPost(args);
                } else if (name === 'update_wp_post') {
                    return await this.updateWpPost(args);
                }
                // Elementor Pro Tools
                else if (name === 'get_elementor_templates') {
                    return await this.getElementorTemplates(args);
                } else if (name === 'apply_elementor_template') {
                    return await this.applyElementorTemplate(args);
                }
                // Amelia Booking Tools
                else if (name === 'get_amelia_services') {
                    return await this.getAmeliaServices(args);
                } else if (name === 'get_amelia_appointments') {
                    return await this.getAmeliaAppointments(args);
                } else if (name === 'create_amelia_appointment') {
                    return await this.createAmeliaAppointment(args);
                } else {
                    throw new McpError(
                        ErrorCode.MethodNotFound,
                        `Unknown tool: ${name}`
                    );
                }
            } catch (error) {
                if (error instanceof McpError) {
                    throw error;
                }

                if (axios.isAxiosError(error)) {
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `API error: ${error.response?.data?.message || error.message}`,
                            },
                        ],
                        isError: true,
                    };
                }

                throw new McpError(
                    ErrorCode.InternalError,
                    `Error executing tool ${name}: ${(error as Error).message}`
                );
            }
        });
    }

    // WordPress Content Tools Implementation
    private async getWpPosts(args: any) {
        const { post_type = 'post', status = 'publish', per_page = 10, page = 1, search } = args;

        const params: Record<string, any> = {
            per_page,
            page,
            status,
        };

        if (search) {
            params.search = search;
        }

        const response = await this.wpAxiosInstance.get(`/${post_type}s`, { params });
        const posts = response.data as WPPost[];

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        total: parseInt(response.headers['x-wp-total'] || '0'),
                        totalPages: parseInt(response.headers['x-wp-totalpages'] || '0'),
                        posts: posts.map(post => ({
                            id: post.id,
                            title: post.title.rendered,
                            excerpt: post.content.rendered.substring(0, 150) + '...',
                            date: post.date,
                            status: post.status,
                            type: post.type,
                            url: `${WP_API_URL}/${post.slug}`,
                        })),
                    }, null, 2),
                },
            ],
        };
    }

    private async createWpPost(args: any) {
        const { title, content, post_type = 'post', status = 'draft', categories, tags } = args;

        const postData: Record<string, any> = {
            title,
            content,
            status,
        };

        if (categories) {
            postData.categories = categories;
        }

        if (tags) {
            postData.tags = tags;
        }

        const response = await this.wpAxiosInstance.post(`/${post_type}s`, postData);
        const post = response.data as WPPost;

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        id: post.id,
                        title: post.title.rendered,
                        status: post.status,
                        url: `${WP_API_URL}/${post.slug}`,
                        message: `${post_type === 'page' ? 'Page' : 'Post'} created successfully.`,
                    }, null, 2),
                },
            ],
        };
    }

    private async updateWpPost(args: any) {
        const { id, title, content, status, categories, tags } = args;

        const postData: Record<string, any> = {};

        if (title) postData.title = title;
        if (content) postData.content = content;
        if (status) postData.status = status;
        if (categories) postData.categories = categories;
        if (tags) postData.tags = tags;

        // Get the post type first
        const getResponse = await this.wpAxiosInstance.get(`/any/${id}`);
        const post = getResponse.data as WPPost;
        const postType = post.type;

        const response = await this.wpAxiosInstance.put(`/${postType}s/${id}`, postData);
        const updatedPost = response.data as WPPost;

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        id: updatedPost.id,
                        title: updatedPost.title.rendered,
                        status: updatedPost.status,
                        url: `${WP_API_URL}/${updatedPost.slug}`,
                        message: `${postType === 'page' ? 'Page' : 'Post'} updated successfully.`,
                    }, null, 2),
                },
            ],
        };
    }

    // Elementor Pro Tools Implementation
    private async getElementorTemplates(args: any) {
        const { template_type, per_page = 10 } = args;

        const params: Record<string, any> = {
            per_page,
        };

        if (template_type) {
            params.meta_key = '_elementor_template_type';
            params.meta_value = template_type;
        }

        const response = await this.wpAxiosInstance.get('/elementor_library', { params });
        const templates = response.data;

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        templates: templates.map((template: any) => ({
                            id: template.id,
                            title: template.title.rendered,
                            type: template.meta?._elementor_template_type || 'unknown',
                            date: template.date,
                        })),
                    }, null, 2),
                },
            ],
        };
    }

    private async applyElementorTemplate(args: any) {
        const { page_id, template_id } = args;

        // This requires custom endpoint or using Elementor's REST API
        // For now, we'll make a custom endpoint assumption
        try {
            const response = await this.wpAxiosInstance.post('/elementor/v1/apply_template', {
                page_id,
                template_id,
            });

            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            success: true,
                            message: 'Template applied successfully',
                            page_id,
                            template_id,
                        }, null, 2),
                    },
                ],
            };
        } catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            success: false,
                            message: 'Template could not be applied. This might require manual application through the Elementor editor.',
                            page_id,
                            template_id,
                        }, null, 2),
                    },
                ],
            };
        }
    }

    // Amelia Booking Tools Implementation
    private async getAmeliaServices(args: any) {
        if (!this.ameliaAxiosInstance) {
            throw new McpError(
                ErrorCode.InternalError,
                'Amelia API credentials not configured'
            );
        }

        const { category_id, status = 'visible' } = args;

        const params: Record<string, any> = {};

        if (category_id) {
            params.categoryId = category_id;
        }

        if (status) {
            params.status = status;
        }

        const response = await this.ameliaAxiosInstance.get('/services', { params });
        const services = response.data as AmeliaService[];

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        services: services.map(service => ({
                            id: service.id,
                            name: service.name,
                            description: service.description,
                            price: service.price,
                            duration: service.duration,
                            categoryId: service.categoryId,
                            status: service.status,
                        })),
                    }, null, 2),
                },
            ],
        };
    }

    private async getAmeliaAppointments(args: any) {
        if (!this.ameliaAxiosInstance) {
            throw new McpError(
                ErrorCode.InternalError,
                'Amelia API credentials not configured'
            );
        }

        const { start_date, end_date, status, customer_email } = args;

        const params: Record<string, any> = {};

        if (start_date) {
            params.dateFrom = start_date;
        }

        if (end_date) {
            params.dateTo = end_date;
        }

        if (status) {
            params.status = status;
        }

        if (customer_email) {
            params.customerEmail = customer_email;
        }

        const response = await this.ameliaAxiosInstance.get('/appointments', { params });
        const appointments = response.data as AmeliaAppointment[];

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        appointments: appointments.map(appointment => ({
                            id: appointment.id,
                            bookingStart: appointment.bookingStart,
                            bookingEnd: appointment.bookingEnd,
                            status: appointment.status,
                            serviceId: appointment.serviceId,
                            providerId: appointment.providerId,
                            customerName: `${appointment.customerFirstName} ${appointment.customerLastName}`,
                            customerEmail: appointment.customerEmail,
                        })),
                    }, null, 2),
                },
            ],
        };
    }

    private async createAmeliaAppointment(args: any) {
        if (!this.ameliaAxiosInstance) {
            throw new McpError(
                ErrorCode.InternalError,
                'Amelia API credentials not configured'
            );
        }

        const {
            service_id,
            provider_id,
            booking_start,
            customer_first_name,
            customer_last_name,
            customer_email,
            customer_phone,
            internal_notes,
        } = args;

        // Get service details to calculate booking end time
        const serviceResponse = await this.ameliaAxiosInstance.get(`/services/${service_id}`);
        const service = serviceResponse.data as AmeliaService;

        const bookingStartDate = new Date(booking_start);
        const bookingEndDate = new Date(bookingStartDate.getTime() + service.duration * 1000);

        const appointmentData = {
            bookingStart: booking_start,
            bookingEnd: bookingEndDate.toISOString(),
            status: 'pending',
            serviceId: service_id,
            providerId: provider_id,
            customer: {
                firstName: customer_first_name,
                lastName: customer_last_name,
                email: customer_email,
                phone: customer_phone,
            },
            internalNotes: internal_notes,
        };

        const response = await this.ameliaAxiosInstance.post('/appointments', appointmentData);

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        id: response.data.id,
                        bookingStart: response.data.bookingStart,
                        bookingEnd: response.data.bookingEnd,
                        status: response.data.status,
                        serviceId: response.data.serviceId,
                        message: 'Appointment created successfully',
                    }, null, 2),
                },
            ],
        };
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('The 7 Space Integration MCP server running on stdio');
    }
}

const server = new The7SpaceIntegrationServer();
server.run().catch(console.error);