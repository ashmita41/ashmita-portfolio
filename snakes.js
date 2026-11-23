(() => {
  const card = document.querySelector("[data-snakes-card]");
  const game = document.getElementById("snake-game");
  if (!card || !game || typeof game.showModal !== "function") return;

  const invite = card.querySelector(".snake-game-invite");
  const open = invite.querySelector(".snake-game-open");
  const board = game.querySelector("[data-snakes-board]");
  const roll = game.querySelector("[data-snakes-roll]");
  const restart = game.querySelector("[data-snakes-reset]");
  const position = game.querySelector("[data-snakes-position]");
  const note = game.querySelector("[data-snakes-note]");
  const close = game.querySelector("[data-snakes-close]");
  const finish = 25;
  const shortcuts = new Map([
    [2, { to: 12, note: "Tests passed on the first try." }],
    [7, { to: 14, note: "The docs actually covered that edge case." }],
    [15, { to: 24, note: "Cached it. Now it flies." }],
    [20, { to: 10, note: "Worked on my machine." }],
    [23, { to: 18, note: "The demo Wi-Fi had other plans." }],
  ]);
  let square = 1;
  let rolls = 0;
  const cells = new Map();
  const svgNS = "http://www.w3.org/2000/svg";

  // Rows alternate direction; both artwork and tile labels use these same coordinates.
  function coords(n) {
    const row = Math.floor((n - 1) / 5);
    const offset = (n - 1) % 5;
    return [row % 2 ? 4 - offset : offset, 4 - row];
  }

  function svg(tag, attrs) {
    const node = document.createElementNS(svgNS, tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
    return node;
  }

  function paintBoard() {
    const ordered = Array.from({ length: finish }, (_, idx) => idx + 1)
      .sort((a, b) => {
        const [ax, ay] = coords(a);
        const [bx, by] = coords(b);
        return ay - by || ax - bx;
      });
    const tiles = document.createDocumentFragment();
    for (const n of ordered) {
      const cell = document.createElement("span");
      cell.className = "snake-game-cell";
      cell.textContent = n;
      if (n === finish) cell.setAttribute("data-finish", "");
      cells.set(n, cell);
      tiles.append(cell);
    }
    const artwork = svg("svg", { class: "snake-game-paths", viewBox: "0 0 500 500", focusable: "false" });
    const ladders = svg("g", { class: "snake-game-ladders", fill: "none", stroke: "currentColor", "stroke-width": "5", "stroke-linecap": "round" });
    const snakes = svg("g", { class: "snake-game-snakes", fill: "none", stroke: "currentColor", "stroke-width": "7", "stroke-linecap": "round" });
    for (const [from, { to }] of shortcuts) {
      const [sx, sy] = coords(from).map((v) => v * 100 + 50);
      const [ex, ey] = coords(to).map((v) => v * 100 + 50);
      const dx = ex - sx;
      const dy = ey - sy;
      const length = Math.hypot(dx, dy);
      const nx = -dy / length;
      const ny = dx / length;
      if (to > from) {
        let lines = "";
        for (const side of [-9, 9]) lines += `M${sx + nx * side},${sy + ny * side}L${ex + nx * side},${ey + ny * side} `;
        const rungs = Math.max(3, Math.round(length / 23));
        for (let i = 0; i <= rungs; i++) {
          const x = sx + dx * (i / rungs);
          const y = sy + dy * (i / rungs);
          lines += `M${x - nx * 9},${y - ny * 9}L${x + nx * 9},${y + ny * 9} `;
        }
        ladders.append(svg("path", { d: lines.trim() }));
      } else {
        snakes.append(svg("path", { d: `M${sx},${sy} C${sx + dx * .26 + nx * 65},${sy + dy * .26 + ny * 65} ${sx + dx * .74 - nx * 60},${sy + dy * .74 - ny * 60} ${ex},${ey}` }),
          svg("circle", { cx: sx, cy: sy, r: "8", fill: "currentColor", stroke: "none" }));
      }
    }
    artwork.append(ladders, snakes);
    board.append(tiles, artwork);
  }

  function update(message) {
    for (const [n, cell] of cells) cell.toggleAttribute("data-player", n === square);
    position.textContent = `Square ${square} of ${finish}${rolls ? ` · Roll ${rolls}` : ""}`;
    note.textContent = message;
    roll.disabled = square === finish;
  }

  open.addEventListener("click", () => {
    if (!cells.size) {
      paintBoard();
      update("Ready when you are.");
    }
    game.showModal();
  });
  close.addEventListener("click", () => game.close());
  game.addEventListener("close", () => open.focus({ preventScroll: true }));
  roll.addEventListener("click", () => {
    if (square === finish) return;
    const dice = 1 + Math.floor(Math.random() * 6);
    const next = square + dice;
    rolls++;
    if (next > finish) {
      update(`Rolled ${dice}. You need a ${finish - square} to land on ${finish}.`);
    } else if (shortcuts.has(next)) {
      const route = shortcuts.get(next);
      square = route.to;
      update(`Rolled ${dice}. ${route.note} ${square > next ? "Ladder up" : "Snake down"} from ${next} to ${square}.`);
    } else {
      square = next;
      update(square === finish ? `Rolled ${dice}. You made it! Ship it. ✨` : `Rolled ${dice}. Keep going!`);
    }
    if (square === finish) restart.focus({ preventScroll: true });
  });
  restart.addEventListener("click", () => {
    square = 1;
    rolls = 0;
    update("Back at the start. Ready for another round?");
    roll.focus({ preventScroll: true });
  });
  card.classList.add("snake-game-ready");
  invite.hidden = false;
})();
