// Copyright (c) OpenAI. All rights reserved.
// Refactored into a modular, function-based library for programmatic use.

const path = require("path");
const fs = require("fs");
const { imageSize } = require("image-size");
const pptxgen = require("pptxgenjs");
const { icon } = require("@fortawesome/fontawesome-svg-core");
const { faHammer } = require("@fortawesome/free-solid-svg-icons"); // Example icon

// --- Constants and Configuration ---
const SLIDE_HEIGHT = 5.625;
const SLIDE_WIDTH = (SLIDE_HEIGHT / 9) * 16;
const BULLET_INDENT = 15;
const FONT_FACE = "Arial";

const FONT_SIZE = {
    PRESENTATION_TITLE: 36, PRESENTATION_SUBTITLE: 12, SLIDE_TITLE: 24,
    DATE: 12, SECTION_TITLE: 16, TEXT: 12, DETAIL: 8,
};

const SLIDE_TITLE_COORDS = { X: 0.3, Y: 0.3, W: "94%" };
const BLACK = "000000";
const LIGHT_GRAY = "f5f5f5";

const PLACEHOLDER_IMG = path.join(__dirname, "placeholder_light_gray_block.png");

// --- Utility Functions ---
const imageInfoCache = new Map();

function getImageDimensions(imagePath) {
    if (imageInfoCache.has(imagePath)) return imageInfoCache.get(imagePath);
    if (!fs.existsSync(imagePath)) {
        console.error(`Warning: Image path not found: ${imagePath}. Using placeholder.`);
        return getImageDimensions(PLACEHOLDER_IMG);
    }
    const dimensions = imageSize(fs.readFileSync(imagePath));
    const info = {
        width: dimensions.width,
        height: dimensions.height,
        aspectRatio: dimensions.width / dimensions.height,
    };
    imageInfoCache.set(imagePath, info);
    return info;
}

function imageSizingCrop(imagePath, x, y, w, h) {
    const { aspectRatio } = getImageDimensions(imagePath);
    const boxAspect = w / h;
    let cx, cy, cw, ch;
    if (aspectRatio >= boxAspect) {
        cw = boxAspect / aspectRatio; ch = 1; cx = (1 - cw) / 2; cy = 0;
    } else {
        cw = 1; ch = aspectRatio / boxAspect; cx = 0; cy = (1 - ch) / 2;
    }
    return { path: imagePath, x, y, w, h, sizing: { type: "crop", x: cx, y: cy, w: cw, h: ch } };
}

function addSlideTitle(slide, title) {
    slide.addText(title, { ...SLIDE_TITLE_COORDS, fontFace: FONT_FACE, fontSize: FONT_SIZE.SLIDE_TITLE, color: BLACK });
}

// --- Slide Creation Functions ---

/**
 * Creates a title slide.
 * @param {pptxgen.Presentation} pptx - The presentation object.
 * @param {object} data - The data for the slide.
 * @param {string} data.title - The main title of the presentation.
 * @param {string} data.subtitle - The subtitle.
 * @param {string} data.date - The date.
 * @param {string} [data.image_path] - Optional path to a background or side image.
 */
function createTitleSlide(pptx, data) {
    const slide = pptx.addSlide();
    slide.background = { color: "FFFFFF" };
    
    const imagePath = data.image_path || PLACEHOLDER_IMG;
    slide.addImage(imageSizingCrop(imagePath, SLIDE_WIDTH * 0.55, SLIDE_HEIGHT * 0.1, SLIDE_WIDTH * 0.45, SLIDE_HEIGHT * 0.8));

    slide.addText(data.title, { x: 0.3, y: "40%", w: "50%", h: 0.75, fontFace: FONT_FACE, fontSize: FONT_SIZE.PRESENTATION_TITLE });
    slide.addText(data.subtitle, { x: 0.3, y: "55%", w: "50%", h: 0.5, fontFace: FONT_FACE, fontSize: FONT_SIZE.PRESENTATION_SUBTITLE });
    slide.addText(data.date, { x: 0.3, y: "90%", w: "50%", h: 0.5, fontFace: FONT_FACE, fontSize: FONT_SIZE.DATE });
}

/**
 * Creates a slide with a stacked column chart and key takeaways.
 * @param {pptxgen.Presentation} pptx - The presentation object.
 * @param {object} data - The data for the slide.
 * @param {string} data.title - The slide title.
 * @param {object} data.chart_data - Data for the chart.
 * @param {string[]} data.takeaways - A list of key takeaway points.
 */
function createChartSlide(pptx, data) {
    const slide = pptx.addSlide();
    slide.background = { color: "FFFFFF" };

    slide.addShape(pptx.ShapeType.rect, { fill: { color: LIGHT_GRAY }, x: "65%", y: 0, w: "35%", h: "100%" });
    addSlideTitle(slide, data.title);
    
    slide.addChart(pptx.ChartType.bar, data.chart_data, { x: SLIDE_TITLE_COORDS.X, y: 1.2, w: "58%", h: 3, barDir: "col", barGrouping: "stacked" });

    const takeawayBullets = data.takeaways.map(t => ({ text: t, options: { bullet: { indent: BULLET_INDENT } } }));
    slide.addText(takeawayBullets, { x: "67%", y: 1.2, w: "29%", h: 4, fontFace: FONT_FACE, fontSize: FONT_SIZE.TEXT });
}

/**
 * Creates a slide with three side-by-side images and captions.
 * @param {pptxgen.Presentation} pptx - The presentation object.
 * @param {object} data - The data for the slide.
 * @param {string} data.title - The slide title.
 * @param {Array<object>} data.items - An array of {image_path, caption}.
 */
function createThreeImageSlide(pptx, data) {
    const slide = pptx.addSlide();
    slide.background = { color: "FFFFFF" };
    addSlideTitle(slide, data.title);

    const GAP = 0.3;
    const TOTAL_WIDTH = SLIDE_WIDTH - 2 * SLIDE_TITLE_COORDS.X;
    const IMG_W = (TOTAL_WIDTH - 2 * GAP) / 3;
    const IMG_H = SLIDE_HEIGHT * 0.5;
    const IMG_Y = (SLIDE_HEIGHT - IMG_H) / 2 - 0.2;
    const CAPTION_Y = IMG_Y + IMG_H + 0.1;

    data.items.forEach((item, i) => {
        const x = SLIDE_TITLE_COORDS.X + i * (IMG_W + GAP);
        const imagePath = item.image_path || PLACEHOLDER_IMG;
        slide.addImage(imageSizingCrop(imagePath, x, IMG_Y, IMG_W, IMG_H));
        slide.addText(item.caption, { x, y: CAPTION_Y, w: IMG_W, h: 1, fontFace: FONT_FACE, fontSize: FONT_SIZE.TEXT });
    });
}


// --- Main Exported Function ---

/**
 * Generates a PowerPoint presentation from a JSON object.
 * @param {object} presentationData - The structured data for the presentation.
 * @param {string} presentationData.output_path - The path to save the .pptx file.
 * @param {Array<object>} presentationData.slides - An array of slide objects.
 * @param {string} slide.type - The type of slide to create (e.g., "title", "chart").
 * @param {object} slide.data - The data for that specific slide.
 */
async function generatePresentation(presentationData) {
    const pptx = new pptxgen();
    pptx.defineLayout({ name: "16x9", width: SLIDE_WIDTH, height: SLIDE_HEIGHT });
    pptx.layout = "16x9";

    const slideGenerators = {
        "title": createTitleSlide,
        "chart": createChartSlide,
        "three_image": createThreeImageSlide,
        // Add other functions from slides_template.js here as needed
    };

    for (const slide of presentationData.slides) {
        const generator = slideGenerators[slide.type];
        if (generator) {
            generator(pptx, slide.data);
        } else {
            console.error(`Unknown slide type: ${slide.type}`);
        }
    }

    await pptx.writeFile({ fileName: presentationData.output_path });
    return { status: "success", path: presentationData.output_path };
}

// This allows the script to be run from the command line for testing.
// e.g., node answer.js '{"output_path": "test.pptx", "slides": [...] }'
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.error("Usage: node answer.js <json_string>");
        process.exit(1);
    }
    const presentationData = JSON.parse(args[0]);
    generatePresentation(presentationData)
        .then(result => console.log(JSON.stringify(result)))
        .catch(err => console.error(err));
}

// Export the main function for use as a library.
module.exports = { generatePresentation };
